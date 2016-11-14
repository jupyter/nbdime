#!/usr/bin/env python
"""A git mergetool plugin for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.

Enable in your global git config with:

    git-nbmergetool config --enable [--global]

Use with:

    git mergetool [<commit> [<commit>]]
"""
import os
import sys
from subprocess import check_call, check_output, CalledProcessError

from . import nbmergeapp
from .args import add_filename_args

def enable(global_=False, set_default=False):
    """Enable nbdime git mergetool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    # Register CLI tool
    check_call(cmd + ['mergetool.nbdime.cmd', 'git-nbmergetool merge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"'])

    # Register webapp tool
    check_call(cmd + ['mergetool.nbdimeweb.cmd', 'git-nbwebmergetool "$BASE" "$LOCAL" "$REMOTE" "$MERGED"'])

    # Common setting:
    check_call(cmd + ['mergetool.prompt', 'false'])

    if set_default:
        # Set default tool to webapp
        check_call(cmd + ['merge.tool', 'nbdimeweb'])



def disable(global_=False, *args):
    """Disable nbdime git mergetool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        previous = check_output(cmd + ['mergetool.nbdime.previous']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        try:
            check_call(cmd + ['--unset', 'merge.tool'])
        except CalledProcessError:
            # already unset
            pass
    else:
        check_call(cmd + ['merge.tool', previous])


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('git-nbmergetool', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    merge_parser = subparsers.add_parser('merge',
        description="The actual entrypoint for the mergetool. Git will call this."
    )

    add_filename_args(merge_parser, ["base", "local", "remote", "merged"])

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime via `git mergetool`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
    )
    config.add_argument('--set-default', action='store_true', dest='set_default',
        help="set nbdimeweb as default mergetool"
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
    if opts.subcommand == 'merge':
        return nbmergeapp.main([opts.base, opts.local, opts.remote, opts.merged])
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_, opts.set_default)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import nbdime.log
    nbdime.log.init_logging()
    main()
