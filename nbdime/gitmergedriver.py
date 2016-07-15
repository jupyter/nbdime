#!/usr/bin/env python
"""A git merge driver for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.
Note that this requires the following to be set in .gitattributes to correctly
identify filetypes with the driver:

    *.ipynb     merge=jupyternotebook

Enable in your global git config with:

    git-nbmergedriver config --enable [--global]

Use with:

    git merge [<commit> [<commit>]]
"""

import sys
from subprocess import check_call, CalledProcessError

from . import nbmergeapp


def enable(global_=False):
    """Enable nbdime git merge driver"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    check_call(cmd + ['merge.jupyternotebook.driver', 'git-nbmergedriver merge %O %A %B %L %P'])
    check_call(cmd + ['merge.jupyternotebook.name', 'jupyter notebook merge driver'])


def disable(global_=False):
    """Disable nbdime git merge drivers"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        check_call(cmd + ['--remove-section', 'merge.jupyternotebook'])
    except CalledProcessError:
        # already unset
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser('git-nbmergedriver', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    merge_parser = subparsers.add_parser('merge',
        description="The actual entrypoint for the merge tool. Git will call this."
    )
    # Argument list
    # we are given base, local remote
    # TODO: support git-config-specified conflict markers inside sources
    merge_parser.add_argument('base')
    merge_parser.add_argument('local')
    merge_parser.add_argument('remote')
    merge_parser.add_argument('marker')
    merge_parser.add_argument('output', nargs='?')

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime for notebooks in `git merge`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
    )
    enable_disable = config.add_mutually_exclusive_group(required=True)
    enable_disable.add_argument('--enable', action='store_const',
        dest='config_func', const=enable,
        help="enable nbdime merge driver via git config"
    )
    enable_disable.add_argument('--disable', action='store_const',
        dest='config_func', const=disable,
        help="disable nbdime merge driver via git config"
    )
    opts = parser.parse_args()
    if opts.subcommand == 'merge':
        opts.output = opts.local
        nbmergeapp.main_merge(opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
