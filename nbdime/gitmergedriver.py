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
import os
import argparse
from subprocess import check_call, check_output, CalledProcessError

from . import nbmergeapp
from .args import add_generic_args, add_diff_args, add_merge_args


def enable(global_=False):
    """Enable nbdime git merge driver"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    check_call(cmd + ['merge.jupyternotebook.driver', 'git-nbmergedriver merge %O %A %B %L %P'])
    check_call(cmd + ['merge.jupyternotebook.name', 'jupyter notebook merge driver'])

    if global_:
        try:
            bpath = check_output(['git', 'config', '--global', 'core.attributesfile'])
            gitattributes = os.path.expanduser(bpath.decode('utf8', 'replace').strip())
        except CalledProcessError:
            gitattributes = os.path.expanduser('~/.gitattributes')
    else:
        # find .gitattributes in current dir
        path = os.path.abspath('.')
        if not os.path.exists(os.path.join(path, '.git')):
            print("No .git directory in %s, skipping git attributes" % path, file=sys.stderr)
            return
        gitattributes = os.path.join(path, '.gitattributes')

    if os.path.exists(gitattributes):
        with open(gitattributes) as f:
            if 'merge=jupyternotebook' in f.read():
                # already written, nothing to do
                return

    with open(gitattributes, 'a') as f:
        f.write('\n*.ipynb\tmerge=jupyternotebook\n')


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
    parser = argparse.ArgumentParser('git-nbmergedriver', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    merge_parser = subparsers.add_parser('merge',
        description="The actual entrypoint for the merge tool. Git will call this."
    )
    add_diff_args(merge_parser)
    add_merge_args(merge_parser)
    # Argument list
    # we are given base, local remote
    # TODO: support git-config-specified conflict markers inside sources
    merge_parser.add_argument('marker')
    merge_parser.add_argument('output', nargs='?')
    # "The merge driver can learn the pathname in which the merged result will
    # be stored via placeholder %P"
    # - NOTE: This is not where the driver should store its output, see below!

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
        # "The merge driver is expected to leave the result of the merge in the
        # file named with %A by overwriting it, and exit with zero status if it
        # managed to merge them cleanly, or non-zero if there were conflicts."
        opts.output = opts.local
        returncode = nbmergeapp.main_merge(opts)
        sys.exit(returncode)
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
