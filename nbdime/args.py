# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import argparse
import logging
import os

from six import PY2

from ._version import __version__
from .log import init_logging, set_nbdime_log_level
from .gitfiles import is_gitref
from .diffing.notebooks import set_notebook_diff_targets


class LogLevelAction(argparse.Action):
    def __init__(self, option_strings, dest, default=None, **kwargs):
        if PY2:
            # __call__ is not called in py2 if option not given:
            level = getattr(logging, default or 'INFO')
            init_logging(level=level)
            set_nbdime_log_level(level)
        super(LogLevelAction, self).__init__(option_strings, dest, default=default, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        level = getattr(logging, values)
        init_logging(level=level)
        set_nbdime_log_level(level)


class SkipAction(argparse.Action):
    """Action of an argument that will not be stored"""
    def __init__(self, option_strings, dest, **kwargs):
        super(SkipAction, self).__init__([], argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, ns, values, opttion_string=None):
        pass


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


def add_generic_args(parser):
    """Adds a set of arguments common to all nbdime commands.
    """
    parser.add_argument(
        '--version',
        action="version",
        version="%(prog)s " + __version__)
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        help="Set the log level by name.",
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
        '-d', '--details',
        action=IgnorableAction,
        help="process/ignore details not covered by other options.")


diff_exclusives = ('sources', 'outputs', 'attachments', 'metadata', 'details')


def add_diff_cli_args(parser):
    """Adds a set of arguments for CLI diff commands (i.e. not web).
    """
    parser.add_argument(
        '--color-words',
        action='store_true', default=False,
        help=("whether to pass the --color-words flag to any internal calls "
              "to git diff")
    )


def add_git_diff_driver_args(diff_parser):
    """Adds a set of 7 stanard git diff driver arguments:
        path old-file old-hex old-mode new-file new-hex new-mode [ rename-to ]

    Note: Only path, base and remote are added to parsed namespace
    """

    diff_parser.add_argument('path')
    diff_parser.add_argument('base', nargs='?', default=None)
    diff_parser.add_argument('base_sha1', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('base_mode', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('remote', nargs='?', default=None)
    diff_parser.add_argument('remote_sha1', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('remote_mode', nargs='?', default=None, action=SkipAction)
    diff_parser.add_argument('rename_to', nargs='?', default=None, action=SkipAction)


def process_diff_flags(args):
    process_exclusive_ignorables(args, diff_exclusives)
    set_notebook_diff_targets(args.sources, args.outputs,
                              args.attachments, args.metadata, args.details)


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
        help="Specify the merge strategy to use.")
    parser.add_argument(
        '--input-strategy',
        default=None,
        choices=cli_conflict_strategies_input,
        help="Specify the merge strategy to use for inputs "
             "(overrides 'merge-strategy' for inputs).")
    parser.add_argument(
        '--output-strategy',
        default=None,
        choices=cli_conflict_strategies_output,
        help="Specify the merge strategy to use for outputs "
             "(overrides 'merge-strategy' for outputs).")
    parser.add_argument(
        '--no-ignore-transients',
        dest='ignore_transients',
        action="store_false",
        default=True,
        help="Disallow deletion of transient data such as outputs and "
             "execution counts in order to resolve conflicts.")


def add_filename_args(parser, names):
    """Add the base, local, remote, and merged positional arguments.

    Helps getting consistent doc strings.
    """
    helps = {
        "notebook": "The notebook filename.",
        "base":   "The base notebook filename.",
        "local":  "The local modified notebook filename.",
        "remote": "The remote modified notebook filename.",
        "merged": "The merge result notebook filename.",
        "patch":  "The patch filename, output from nbdiff.",
        }
    for name in names:
        parser.add_argument(name, help=helps[name])


def args_for_server(arguments):
    """Translate standard arguments into kwargs for running webapp.nbdimeserver.main"""
    # Map format: <arguments.name>='<kwargs[key]>'
    kmap = dict(ip='ip',
                port='port',
                workdirectory='cwd',
                base_url='base_url',
                )
    return {kmap[k]: v for k, v in vars(arguments).items() if k in kmap}


def args_for_browse(arguments):
    """Translate standard arguments into kwargs for webapp.webutil.browse()"""
    # Map format: <arguments.name>='<kwargs[key]>'
    kmap = dict(ip='ip',
                browser='browsername',
                base_url='base_url',
                )
    return {kmap[k]: v for k, v in vars(arguments).items() if k in kmap}
