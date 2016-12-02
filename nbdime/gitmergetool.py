#!/usr/bin/env python
"""A git mergetool plugin for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.

Enable in your global git config with:

    git-nbmergetool config --enable [--global]

Use with:

    git mergetool [<commit> [<commit>]]
"""
import sys
from subprocess import check_call, check_output, CalledProcessError

import nbdime.log
from .webapp import nbmergetool
from .args import add_filename_args, add_generic_args


def enable(global_=False, set_default=False):
    """Enable nbdime git mergetool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    # Register CLI tool
    check_call(cmd + ['mergetool.nbdime.cmd', 'git-nbmergetool merge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"'])

    # Common setting:
    check_call(cmd + ['mergetool.prompt', 'false'])

    if set_default:
        # Set default tool to webapp
        check_call(cmd + ['merge.tool', 'nbdime'])


def disable(global_=False, *args):
    """Disable nbdime git mergetool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        check_call(cmd + ['--unset', 'merge.tool'])
    except CalledProcessError:
        # already unset
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('git-nbmergetool', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_generic_args(parser)
    subparsers = parser.add_subparsers(dest='subcommand')

    merge_parser = subparsers.add_parser('merge',
        description="The actual entrypoint for the mergetool. Git will call this."
    )
    nbmergetool.build_arg_parser(merge_parser)

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime via `git mergetool`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
    )
    config.add_argument('--set-default', action='store_true', dest='set_default',
        help="set nbdime as default mergetool"
    )
    enable_disable = config.add_mutually_exclusive_group(required=True)
    enable_disable.add_argument('--enable', action='store_const',
        dest='config_func', const=enable,
        help="enable nbdime mergetool via git config"
    )
    enable_disable.add_argument('--disable', action='store_const',
        dest='config_func', const=disable,
        help="disable nbdime mergetool via git config"
    )
    opts = parser.parse_args(args)
    nbdime.log.init_logging(level=opts.log_level)
    if opts.subcommand == 'merge':
        return nbmergetool.main_parsed(opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_, opts.set_default)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
