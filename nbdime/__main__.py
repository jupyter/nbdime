# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from subprocess import call

import nbdime
from ._version import __version__

from shutil import which

COMMANDS = ["show", "diff", "merge", "diff-web", "merge-web", "mergetool",
            "config-git", "extensions"]
HELP_MESSAGE_VERBOSE = ("Usage: nbdime [OPTIONS]\n\n"
                       "OPTIONS: -h, --version, COMMANDS{%s}\n\n"
                       "Examples: nbdime --version\n"
                       "          nbdime show -h\n"
                       "          nbdime merge-web\n\n"
                       "          nbdime config-git (--enable | --disable)\n"
                       "          nbdime extensions (--enable | --disable)\n\n"
                       "Documentation: https://nbdime.readthedocs.io" % ", ".join(COMMANDS))


def main_mergetool(args):
    if not which('git'):
        sys.exit("Cannot use \"nbdime mergetool\" alias as git is not preset on path")
    to_call = 'git mergetool --tool=nbdime'.split()

    if args:
        paths = [a for a in args if a.endswith(".ipynb")]
        if len(paths) != len(args):
            nbdime.log.warning("Skipping given filenames without .ipynb extension: %r", [a for a in args if a not in paths])
    else:
        paths = ["*.ipynb"]
    to_call.extend(paths)

    nbdime.log.info("Calling 'git mergetool --tool=nbdime' on files %r", paths)

    return call(to_call)


def toggle_extensions(enable, args):
    if enable:
        call('jupyter serverextension enable --py nbdime'.split() + args)
        call('jupyter nbextension install --py nbdime'.split() + args)
        call('jupyter nbextension enable --py nbdime'.split() + args)
        call('jupyter labextension install nbdime-jupyterlab'.split() + args)
    else:
        call('jupyter serverextension disable --py nbdime'.split() + args)
        call('jupyter nbextension disable --py nbdime'.split() + args)
        call('jupyter nbextension uninstall --py nbdime'.split() + args)
        call('jupyter labextension uninstall nbdime-jupyterlab'.split() + args)


def main_dispatch(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) < 1:
        sys.exit("Option missing.\n\n%s" % HELP_MESSAGE_VERBOSE)

    cmd = args[0]
    args = args[1:]

    if cmd == "show":
        from nbdime.nbshowapp import main
    elif cmd == "diff":
        from nbdime.nbdiffapp import main
    elif cmd == "merge":
        from nbdime.nbmergeapp import main
    elif cmd == "diff-web":
        from nbdime.webapp.nbdiffweb import main
    elif cmd == "merge-web":
        from nbdime.webapp.nbmergeweb import main
    elif cmd == 'mergetool':
        main = main_mergetool
    elif cmd == 'server':
        from nbdime.webapp.nbdimeserver import main
    elif cmd == 'config-git':
        # Call all git configs
        from nbdime.vcs.git.diffdriver import main as diff_driver
        from nbdime.vcs.git.difftool import main as diff_tool
        from nbdime.vcs.git.mergedriver import main as merge_driver
        from nbdime.vcs.git.mergetool import main as merge_tool
        args = ['config'] + args
        # Short-circuit on first non-zero return code:
        return (
            diff_driver(args) or
            merge_driver(args) or
            diff_tool(args) or
            merge_tool(args)
        )
    elif cmd == 'reg-extensions':
        # Register nbdime extensions
        toggle_extensions(True, args)
        return 0
    elif cmd == 'extensions':
        subcmd = args.pop(0)
        if subcmd == '--enable':
            # Register nbdime extensions
            toggle_extensions(True, args)
        elif subcmd == '--disable':
            # Unregister nbdime extensions
            toggle_extensions(False, args)
        else:
            sys.exit(
                'Unknown command: use either "--enable" or "--disable" '
                'with "nbdime extensions", not %r' % subcmd)
        return 0
    else:
        if cmd == '--version':
            sys.exit(__version__)
        if cmd == '-h' or cmd == '--help':
            sys.exit(HELP_MESSAGE_VERBOSE)
        if cmd == '--config':
            # List all possible config options:
            from .args import modify_config_for_print
            from .config import build_config, entrypoint_configurables
            from .prettyprint import pretty_print_dict, PrettyPrintConfig
            print('All available config options, and their current values:\n',
                  file=sys.stderr)
            for entrypoint, cls in entrypoint_configurables.items():
                config = build_config(entrypoint, True)
                pretty_print_dict({
                        cls.__name__: modify_config_for_print(config),
                    },
                    config=PrettyPrintConfig(out=sys.stderr)
                )
                print('', file=sys.stderr)
            sys.exit(1)
        else:
            sys.exit("Unrecognized command '%s'\n\n%s." %
                     (cmd, HELP_MESSAGE_VERBOSE))
    return main(args)


if __name__ == "__main__":
    # This is triggered by "python -m nbdime <args>"
    sys.exit(main_dispatch())
