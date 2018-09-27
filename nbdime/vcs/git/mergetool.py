#!/usr/bin/env python
"""A git mergetool plugin for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.

Enable in your global git config with:

    git-nbmergetool config --enable [--global | --system]

Use with:

    git mergetool [<commit> [<commit>]]
"""
import sys
from subprocess import check_call, CalledProcessError

from nbdime.webapp import nbmergetool
from nbdime.args import add_generic_args, add_git_config_subcommand, ConfigBackedParser


def enable(scope=None, set_default=False):
    """Enable nbdime git mergetool"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)

    # Register CLI tool
    check_call(cmd + ['mergetool.nbdime.cmd', 'git-nbmergetool merge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"'])

    # Common setting:
    check_call(cmd + ['mergetool.prompt', 'false'])

    if set_default:
        # Set default tool to webapp
        check_call(cmd + ['merge.tool', 'nbdime'])


def disable(scope=None, _=None):
    """Disable nbdime git mergetool"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)
    try:
        check_call(cmd + ['--unset', 'merge.tool'])
    except CalledProcessError:
        # already unset
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = ConfigBackedParser('git-nbmergetool', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_generic_args(parser)
    subparsers = parser.add_subparsers(dest='subcommand')

    merge_parser = subparsers.add_parser('merge',
        description="The actual entrypoint for the mergetool. Git will call this."
    )
    nbmergetool.build_arg_parser(merge_parser)

    config = add_git_config_subcommand(subparsers,
        enable, disable,
        subparser_help="Configure git to use nbdime via `git mergetool`",
        enable_help="enable nbdime mergetool via git config",
        disable_help="disable nbdime mergetool via git config")
    config.add_argument('--set-default', action='store_true', dest='set_default',
        help="set nbdime as default mergetool"
    )

    opts = parser.parse_args(args)
    if opts.subcommand == 'merge':
        return nbmergetool.main_parsed(opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.scope, opts.set_default)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
