# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import argparse
import json
import logging
import os
import sys

from ._version import __version__
from .config import (
    get_defaults_for_argparse, build_config, entrypoint_configurables,
    Namespace
)
from .diffing.notebooks import set_notebook_diff_targets, set_notebook_diff_ignores
from .gitfiles import is_gitref
from .ignorables import diff_ignorables
from .log import init_logging, set_nbdime_log_level


class ConfigBackedParser(argparse.ArgumentParser):

    def parse_known_args(self, args=None, namespace=None):
        entrypoint = self.prog.split(' ')[0]
        try:
            defs = get_defaults_for_argparse(entrypoint)
            ignore = defs.pop('Ignore', None)
            self.set_defaults(**defs)
            if ignore:
                set_notebook_diff_ignores(ignore)
        except ValueError:
            pass
        return super(ConfigBackedParser, self).parse_known_args(args=args, namespace=namespace)


class LogLevelAction(argparse.Action):
    def __init__(self, option_strings, dest, default=None, **kwargs):
        # __call__ is not called if option not given:
        level = getattr(logging, default or 'INFO')
        init_logging(level=level)
        set_nbdime_log_level(level)
        super(LogLevelAction, self).__init__(option_strings, dest, default=default, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        level = getattr(logging, values)
        set_nbdime_log_level(level, True)


class SkipAction(argparse.Action):
    """Action of an argument that will not be stored"""
    def __init__(self, option_strings, dest, **kwargs):
        super(SkipAction, self).__init__([], argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, ns, values, opttion_string=None):
        pass


class PathType(object):
    """Argparse type for arguments that should be paths

    No-op on Python 3, but casts Python 2 bytes to text
    using sys.getfilesystemencoding()
    """
    def __init__(self):
        pass

    def __call__(self, value):
        if not isinstance(value, bytes):
            return value

        # py2: decode bytes to text
        encoding = sys.getfilesystemencoding() or 'utf-8'
        if encoding.lower() == 'ascii':
            # ignore ascii and use utf-8
            # if it really is ascii, this will still be correct,
            # but it never should actually be ascii
            encoding = 'utf-8'

        return value.decode(encoding)


Path = PathType()


def modify_config_for_print(config):
    output = {}
    ns = None
    for k, v in config.items():
        if isinstance(v, dict):
            output[k] = modify_config_for_print(v)
            if not output[k]:
                output[k] = '{}'
        elif k in diff_ignorables and v is None:
            if ns is None:
                ns = Namespace(config)
                for k2 in diff_ignorables:
                    setattr(ns, k2, config.get(k2, None))
                process_exclusive_ignorables(ns, diff_ignorables)
            output[k] = '<unset, resolves to {0}>'.format(
                json.dumps(getattr(ns, k, v)))
        else:
            output[k] = json.dumps(v)
    return output


class ConfigHelpAction(argparse.Action):
    def __init__(self, option_strings, dest, help=None):
        super(ConfigHelpAction, self).__init__(
            option_strings, dest, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        from .prettyprint import pretty_print_dict, PrettyPrintConfig

        header = entrypoint_configurables[parser.prog].__name__
        config = build_config(parser.prog, True)
        pretty_print_dict(
            {
                header: modify_config_for_print(config),
            },
            config=PrettyPrintConfig(out=sys.stderr)
        )
        sys.exit(1)


class IgnorableAction(argparse.Action):
    """Adds the supplied positive options and negative/ignore version as well"""

    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        opts = []
        for opt in option_strings:
            if len(opt) == 2 and opt[0] == '-':
                if not opt[1].islower():
                    raise ValueError('Single character flags should be lower-case for IgnorableAction')
                opts.append(opt)
                opts.append(opt.upper())
            elif opt[:2] == '--':
                opts.append(opt)
                opts.append('--ignore-' + opt[2:])
            else:
                ValueError('Could not turn option "%s" into an IgnoreAction option.')

        # Put positives first, negatives last:
        opts = opts[0::2] + opts[1::2]

        super(IgnorableAction, self).__init__(
            opts, dest, nargs=0, const=None,
            default=default, required=required,
            help=help)

    def __call__(self, parser, ns, values, option_string=None):
        if len(option_string) == 2:
            setattr(ns, self.dest, option_string[1].islower())
        else:
            setattr(ns, self.dest, option_string[2 : 2 + len('ignore')] != 'ignore')


def process_exclusive_ignorables(ns, arg_names, default=True):
    """Parse a set of ignorables.

    It checks that all specified options are either all positive or all negative.
    It then returns a namespace with the parsed options.

    Returns whether any values were specified or not.
    """
    # `toggle` tracks whether:
    #  - True: One or more positive options were defined
    #  - False: One or more negative options were defined
    #  - None: No options were defined
    toggle = getattr(ns, arg_names[0])
    for name in arg_names[1:]:
        opt = getattr(ns, name)
        if toggle is None:
            toggle = opt
        elif toggle != opt and opt is not None:
            message = 'Arguments must either all be negative or all positive: %r' % (arg_names,)
            raise argparse.ArgumentError(None, message)

    if toggle is not None:
        # One or more options were defined, set default to the opposite
        default = not toggle

    # Set all unset options to the default
    for name in arg_names:
        if getattr(ns, name) is None:
            setattr(ns, name, default)
    return toggle is not None


def add_generic_args(parser):
    """Adds a set of arguments common to all nbdime commands.
    """
    parser.add_argument(
        '--version',
        action="version",
        version="%(prog)s " + __version__)
    parser.add_argument(
        '--config',
        help="list the valid config keys and their current effective values",
        action=ConfigHelpAction,
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        help="set the log level by name.",
        action=LogLevelAction,
    )


def add_git_config_subcommand(subparsers, enable, disable, subparser_help, enable_help, disable_help):
    # Add subparser
    config = subparsers.add_parser('config',
        description=subparser_help)

    # Option for git scope (global/system):
    scope = config.add_mutually_exclusive_group()
    scope.add_argument('--global', action='store_const', dest='scope',
        const='global',
        help="configure your global git config instead of the current repo"
    )
    scope.add_argument('--system', action='store_const', dest='scope',
        const='system',
        help="configure your system git config instead of the current repo"
    )

    # Add enable/disable flags
    enable_disable = config.add_mutually_exclusive_group(required=True)
    enable_disable.add_argument('--enable', action='store_const',
        dest='config_func', const=enable,
        help=enable_help
    )
    enable_disable.add_argument('--disable', action='store_const',
        dest='config_func', const=disable,
        help=disable_help
    )
    return config


def add_web_args(parser, default_port=8888):
    """Adds a set of arguments common to all commands that show a web gui.
    """
    port_help = (
        "specify the port you want the server to run on. Default is %d%s." % (
            default_port, " (random)" if default_port == 0 else ""
        ))
    parser.add_argument(
        '-p', '--port',
        default=default_port,
        type=int,
        help=port_help)
    parser.add_argument(
        '-b', '--browser',
        default=None,
        type=str,
        help="specify the browser to use, to override the system default.")
    parser.add_argument(
        '--persist',
        action="store_true",
        default=False,
        help="prevent server shutting down on remote close request (when these"
             " would normally be supported)."
    )
    parser.add_argument(
        '--ip',
        default='127.0.0.1',
        help="specify the interface to listen to for the web server. "
        "NOTE: Setting this to anything other than 127.0.0.1/localhost "
        "might comprimise the security of your computer. Use with care!")
    cwd = os.path.abspath(os.path.curdir)

    parser.add_argument(
        '-w', '--workdirectory',
        default=cwd,
        help="specify the working directory you want "
             "the server to run from. Default is the "
             "actual cwd at program start.")
    parser.add_argument(
        '--base-url',
        default='/',
        help="The base URL prefix under which to run the web app")
    parser.add_argument(
        '--show-unchanged',
        dest='hide_unchanged',
        action="store_false",
        default=True,
        help="show unchanged cells by default"
    )
    parser.add_argument(
        '--identical-lines-margin',
        dest='identical_lines_margin',
        default=2,
        type=int,
        help="Margin for collapsing identical lines in editor; set to -1 to deactivate.",
    )


def add_diff_args(parser):
    """Adds a set of arguments for commands that perform diffs.

    Note:
        Merge applications also performs diff operations to compute
        the merge, so these arguments should also be included there.
    """
    # TODO: Define sensible strategy variables and implement
    #parser.add_argument('-X', '--diff-strategy',
    #                    default="default", choices=("foo", "bar"),
    #                    help="specify the diff strategy to use.")

    # Things we can choose to diff or not
    ignorables = parser.add_argument_group(
        title='ignorables',
        description='Set which parts of the notebook (not) to process.')
    ignorables.add_argument(
        '-s', '--sources',
        action=IgnorableAction,
        help="process/ignore sources.")
    ignorables.add_argument(
        '-o', '--outputs',
        action=IgnorableAction,
        help="process/ignore outputs.")
    ignorables.add_argument(
        '-a', '--attachments',
        action=IgnorableAction,
        help="process/ignore attachments.")
    ignorables.add_argument(
        '-m', '--metadata',
        action=IgnorableAction,
        help="process/ignore metadata.")
    ignorables.add_argument(
        '-i', '--id',
        action=IgnorableAction,
        help="process/ignore identifiers.")
    ignorables.add_argument(
        '-d', '--details',
        action=IgnorableAction,
        help="process/ignore details not covered by other options.")


def add_diff_cli_args(parser):
    """Adds a set of arguments for CLI diff commands (i.e. not web).
    """
    parser.add_argument(
        '--color-words',
        action='store_true', default=False,
        help=("whether to pass the --color-words flag to any internal calls "
              "to git diff")
    )


def add_filter_args(diff_parser):
    """Adds configuration for git commands where filter use is flagged"""
    # Ideally, we would want to apply the filter only if we knew
    # the file was not from a blob. However, this is not possible:
    # If remote file path is equal to repo file path, it implies
    # that the hex of remote equals the hex of the file on disk.
    # Two possible cases can cause this:
    # 1) Diffing against working dir (or stage when entire file is staged)
    # 2) Diffing against a blob (clean) that happens to have the same hex as
    #    the (smudged) file in working tree.
    # Condition 1 should have filter applied, 2 should not.
    # We can learn something by comparing the remote hash to the hash of the
    # file in HEAD.
    # - If they are equal, we know that is cannot come from a diff
    #   agains working tree (git would not see it as changed),
    #   so it must be from a blob (clean). No filter.
    # - If they differ, consider the setup:
    #   git co A; git co B -- file.path; git reset A
    #   + remote could be from a working-tree diff: git diff (smudged, apply filter).
    #   + remote could be from a blob: git diff A B (clean, no filter).
    #
    # These are undistinguishable to us. Therefore, we will always
    # apply the filter to the remote file if flag use_filter is set.
    diff_parser.add_argument(
        '--use-filter',
        action='store_true', default=False,
        help='apply any configured git filters on remote')


def add_git_diff_driver_args(diff_parser):
    """Adds a set of 7 stanard git diff driver arguments:
        path old-file old-hex old-mode new-file new-hex new-mode [ rename-to rename-metadata ]

    Note: Only path, base and remote are added to parsed namespace
    """
    add_filter_args(diff_parser)
    diff_parser.add_argument('path', type=Path)
    diff_parser.add_argument('base', type=Path, nargs='?', default=None)
    diff_parser.add_argument('base_sha1', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('base_mode', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('remote', type=Path, nargs='?', default=None)
    diff_parser.add_argument('remote_sha1', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('remote_mode', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('rename_to', type=Path, nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('rename_metadata', type=Path, nargs='?', default=None, action=SkipAction)


def process_diff_flags(args):
    any_flags_given = process_exclusive_ignorables(args, diff_ignorables)
    if any_flags_given:
        # Note: This will blow away any options set via config (for these fields)
        set_notebook_diff_targets(
            args.sources, args.outputs, args.attachments, args.metadata,
            args.id, args.details)


def resolve_diff_args(args):
    """Resolve ambiguity of path vs base/remote for git:

    Cases:
     - No args: Use defaults
     - One arg: Either base or path, check with is_gitref.
     - Two args or more: Check if first two are base/remote by is_gitref
    """
    base = args.base
    remote = args.remote
    paths = getattr(args, 'paths', None)
    if not paths:
        paths = None
    if remote is None and paths is None:
        # One arg only:
        if not is_gitref(base):
            paths = base
            base = 'HEAD'
    # Two or more args:
    elif paths is None:
        # Two exactly
        # - Two files (not git-mode, do nothing)
        # - Base gitref one file (remote=None, path = file)
        # - Base gitref remote gitref (do nothing)
        if is_gitref(base) and not is_gitref(remote):
            paths = remote
            remote = None
    elif base and remote:
        # Three or more
        if not is_gitref(base):
            paths = [base, remote] + paths
            base = remote = None
        elif is_gitref(base) and not is_gitref(remote):
            paths = [remote] + paths
            remote = None
    return base, remote, paths


def add_merge_args(parser):
    """Adds a set of arguments for commands that perform merges.
    """
    from .merging.notebooks import cli_conflict_strategies, cli_conflict_strategies_input, cli_conflict_strategies_output
    parser.add_argument(
        '--merge-strategy',
        default="inline",
        choices=cli_conflict_strategies,
        help="the merge strategy to use.")
    parser.add_argument(
        '--input-strategy',
        default=None,
        choices=cli_conflict_strategies_input,
        help="the merge strategy to use for inputs "
             "(overrides 'merge-strategy' for inputs).")
    parser.add_argument(
        '--output-strategy',
        default=None,
        choices=cli_conflict_strategies_output,
        help="the merge strategy to use for outputs "
             "(overrides 'merge-strategy' for outputs).")
    parser.add_argument(
        '--no-ignore-transients',
        dest='ignore_transients',
        action="store_false",
        default=True,
        help="disallow deletion of transient data such as outputs and "
             "execution counts in order to resolve conflicts.")


filename_help = {
    "notebook": "The notebook filename.",
    "base":   "The base notebook filename.",
    "local":  "The local modified notebook filename.",
    "remote": "The remote modified notebook filename.",
    "merged": "The merge result notebook filename.",
    "patch":  "The patch filename, output from nbdiff.",
    }


def add_filename_args(parser, names):
    """Add the base, local, remote, and merged positional arguments.

    Helps getting consistent doc strings.
    """
    for name in names:
        parser.add_argument(name, type=Path, help=filename_help[name])


def add_prettyprint_args(parser):
    """Adds optional arguments for controlling pretty print behavior.
    """
    parser.add_argument(
        '--no-color',
        dest='use_color',
        action="store_false",
        default=True,
        help=("prevent use of ANSI color code escapes for text output")
    )
    parser.add_argument(
        '--no-git',
        dest='use_git',
        action="store_false",
        default=True,
        help=("prevent use of git for formatting diff/merge text output")
    )
    parser.add_argument(
        '--no-use-diff',
        dest='use_diff',
        action="store_false",
        default=True,
        help=("prevent use of diff/diff3 for formatting diff/merge text output")
    )


def prettyprint_config_from_args(arguments, **kwargs):
    from .prettyprint import PrettyPrintConfig
    return PrettyPrintConfig(
        include=arguments,
        color_words=getattr(arguments, 'color_words', False),
        use_color=getattr(arguments, 'use_color', True),
        use_git=getattr(arguments, 'use_git', True),
        use_diff=getattr(arguments, 'use_diff', True),
        **kwargs
    )


def args_for_server(arguments):
    """Translate standard arguments into kwargs for running webapp.nbdimeserver.main"""
    # Map format: <arguments.name>='<kwargs[key]>'
    kmap = dict(ip='ip',
                port='port',
                workdirectory='cwd',
                base_url='base_url',
                hide_unchanged='hide_unchanged',
                identical_lines_margin='identical_lines_margin',
                )
    ret = {kmap[k]: v for k, v in vars(arguments).items() if k in kmap}
    if 'persist' in arguments:
        ret['closable'] = not arguments.persist
    return ret


def args_for_browse(arguments):
    """Translate standard arguments into kwargs for webapp.webutil.browse()"""
    # Map format: <arguments.name>='<kwargs[key]>'
    kmap = dict(ip='ip',
                browser='browsername',
                base_url='base_url',
                )
    return {kmap[k]: v for k, v in vars(arguments).items() if k in kmap}
