#!/usr/bin/env python
"""A git diff driver for notebooks.

Uses nbdime to create diffs for notebooks instead of plain text diffs of JSON.
Note that this requires the following to be set in .gitattributes to correctly
identify filetypes with the driver:

    *.ipynb     diff=jupyternotebook

Enable in your global git config with:

    git-nbdiffdriver config --enable [--global]

Use with:

    git diff [<commit> [<commit>]]
"""

from __future__ import print_function

import io
import os
import sys
from subprocess import check_call, check_output, CalledProcessError

from . import nbdiffapp
from .utils import locate_gitattributes

def enable(global_=False):
    """Enable nbdime git diff driver"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    check_call(cmd + ['diff.jupyternotebook.command', 'git-nbdiffdriver diff'])
    gitattributes = locate_gitattributes(global_)
    if gitattributes is None:
        print("No .git directory in %s, skipping git attributes" % path, file=sys.stderr)
        return

    if os.path.exists(gitattributes):
        with io.open(gitattributes, encoding="utf8") as f:
            if 'diff=jupyternotebook' in f.read():
                # already written, nothing to do
                return

    with io.open(gitattributes, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tdiff=jupyternotebook\n')


def disable(global_=False):
    """Disable nbdime git diff drivers"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        check_call(cmd + ['--remove-section', 'diff.jupyternotebook'])
    except CalledProcessError:
        # already unset
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('git-nbdiffdriver', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    # Argument list
    # path old-file old-hex old-mode new-file new-hex new-mode [ rename-to ]
    diff_parser.add_argument('path')
    diff_parser.add_argument('a', nargs='?', default=None)
    diff_parser.add_argument('a_sha1', nargs='?', default=None)
    diff_parser.add_argument('a_mode', nargs='?', default=None)
    diff_parser.add_argument('b', nargs='?', default=None)
    diff_parser.add_argument('b_sha1', nargs='?', default=None)
    diff_parser.add_argument('b_mode', nargs='?', default=None)
    diff_parser.add_argument('rename_to', nargs='?', default=None)

    # TODO: From git docs: "For a path that is unmerged, GIT_EXTERNAL_DIFF is called with 1 parameter, <path>."

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime for notebooks in `git diff`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
    )
    enable_disable = config.add_mutually_exclusive_group(required=True)
    enable_disable.add_argument('--enable', action='store_const',
        dest='config_func', const=enable,
        help="enable nbdime diff driver via git config"
    )
    enable_disable.add_argument('--disable', action='store_const',
        dest='config_func', const=disable,
        help="disable nbdime diff driver via git config"
    )
    opts = parser.parse_args(args)
    if opts.subcommand == 'diff':
        return nbdiffapp.main([opts.a, opts.b])
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
