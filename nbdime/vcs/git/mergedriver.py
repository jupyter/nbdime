#!/usr/bin/env python
"""A git merge driver for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.
Note that this requires the following to be set in .gitattributes to correctly
identify filetypes with the driver:

    *.ipynb     merge=jupyternotebook

Enable in your global git config with:

    git-nbmergedriver config --enable [--global | --system]

Use with:

    git merge [<commit> [<commit>]]
"""



import argparse
import io
import os
import sys
from subprocess import check_call, CalledProcessError

from nbdime import nbmergeapp
from nbdime.args import (
    add_generic_args, add_diff_args, add_merge_args, add_filename_args,
    add_git_config_subcommand, ConfigBackedParser,
)
from nbdime.utils import locate_gitattributes, ensure_dir_exists


def enable(scope=None):
    """Enable nbdime git merge driver"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)

    check_call(cmd + ['merge.jupyternotebook.driver', 'git-nbmergedriver merge %O %A %B %L %P'])
    check_call(cmd + ['merge.jupyternotebook.name', 'jupyter notebook merge driver'])

    gitattributes = locate_gitattributes(scope)
    if gitattributes is None:
        assert scope is None, "No gitattributes found for scope: %s" % scope
        print("No .git directory in %s, skipping git attributes" % os.curdir, file=sys.stderr)
        return

    if os.path.exists(gitattributes):
        with io.open(gitattributes, encoding="utf8") as f:
            if 'merge=jupyternotebook' in f.read():
                # already written, nothing to do
                return
    else:
        ensure_dir_exists(os.path.dirname(gitattributes))

    with io.open(gitattributes, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tmerge=jupyternotebook\n')


def disable(scope=None):
    """Disable nbdime git merge drivers"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)
    try:
        check_call(cmd + ['--remove-section', 'merge.jupyternotebook'])
    except CalledProcessError:
        # already unset
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = ConfigBackedParser('git-nbmergedriver', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    merge_parser = subparsers.add_parser('merge',
        description="The actual entrypoint for the merge tool. Git will call this."
    )
    add_generic_args(parser)
    add_diff_args(merge_parser)
    add_merge_args(merge_parser)

    # Argument list, we are given base, local, remote
    add_filename_args(merge_parser, ["base", "local", "remote"])

    # TODO: support git-config-specified conflict markers inside sources
    merge_parser.add_argument('marker')
    merge_parser.add_argument('out', nargs='?')
    # "The merge driver can learn the pathname in which the merged result will
    # be stored via placeholder %P"
    # - NOTE: This is not where the driver should store its output, see below!


    add_git_config_subcommand(
        subparsers,
        enable, disable,
        subparser_help="Configure git to use nbdime for notebooks in `git merge`",
        enable_help="enable nbdime merge driver via git config",
        disable_help="disable nbdime merge driver via git config")

    opts = parser.parse_args(args)
    if opts.subcommand == 'merge':
        # "The merge driver is expected to leave the result of the merge in the
        # file named with %A by overwriting it, and exit with zero status if it
        # managed to merge them cleanly, or non-zero if there were conflicts."
        opts.out = opts.local
        # mergeapp expects an additional decisions arg:
        opts.decisions = False
        return nbmergeapp.main_merge(opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.scope)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
