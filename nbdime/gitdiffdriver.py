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
from subprocess import check_call, CalledProcessError

from . import nbdiffapp
from .args import add_git_config_subcommand
from .utils import locate_gitattributes, ensure_dir_exists


def enable(scope=None):
    """Enable nbdime git diff driver"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)

    check_call(cmd + ['diff.jupyternotebook.command', 'git-nbdiffdriver diff'])
    gitattributes = locate_gitattributes(scope)
    if gitattributes is None:
        assert scope is None, "No gitattributes found for scope: %s" % scope
        print("No .git directory in %s, skipping git attributes" % os.curdir, file=sys.stderr)
        return

    if os.path.exists(gitattributes):
        with io.open(gitattributes, encoding="utf8") as f:
            if 'diff=jupyternotebook' in f.read():
                # already written, nothing to do
                return
    else:
        ensure_dir_exists(os.path.dirname(gitattributes))

    with io.open(gitattributes, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tdiff=jupyternotebook\n')


def disable(scope=None):
    """Disable nbdime git diff drivers"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)
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
    config = add_git_config_subcommand(subparsers,
        enable, disable,
        subparser_help="Configure git to use nbdime for notebooks in `git diff`",
        enable_help="enable nbdime diff driver via git config",
        disable_help="disable nbdime diff driver via git config")

    opts = parser.parse_args(args)
    if opts.subcommand == 'diff':
        return nbdiffapp.main([opts.a, opts.b])
    elif opts.subcommand == 'config':
        opts.config_func(opts.scope)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
