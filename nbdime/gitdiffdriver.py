#!/usr/bin/env python
"""A git diff driver for notebooks.

Uses nbdime to create diffs for notebooks instead of plain text diffs of JSON.
Note that this requires the following to be set in .gitattributes to correctly
identify filetypes with the driver:

    *.ipynb     diff=jupyternotebook

Enable in your global git config with:

    git-nbdiffdriver config --enable [--global | --system]

Use with:

    git diff [<commit> [<commit>]]
"""

from __future__ import print_function

import io
import os
import sys
from subprocess import check_call, CalledProcessError

from .args import (
    add_git_config_subcommand, add_generic_args, add_diff_args, add_web_args,
    add_git_diff_driver_args, diff_exclusives, web_args)
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
    add_generic_args(parser)

    subparsers = parser.add_subparsers(dest='subcommand')

    webdiff_parser = subparsers.add_parser('webdiff',
        description="The actual entrypoint for the webdiff tool. Git will call this."
    )
    add_diff_args(webdiff_parser)
    add_web_args(webdiff_parser, 0)
    add_git_diff_driver_args(webdiff_parser)

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    add_diff_args(diff_parser)
    add_git_diff_driver_args(diff_parser)

    # TODO: From git docs: "For a path that is unmerged, GIT_EXTERNAL_DIFF is called with 1 parameter, <path>."
    config = add_git_config_subcommand(subparsers,
        enable, disable,
        subparser_help="Configure git to use nbdime for notebooks in `git diff`",
        enable_help="enable nbdime diff driver via git config",
        disable_help="disable nbdime diff driver via git config")

    opts = parser.parse_args(args)
    if opts.subcommand == 'diff':
        from . import nbdiffapp
        return nbdiffapp.main(
            [opts.a, opts.b] +
            ['--%s' % name for name in diff_exclusives if getattr(opts, name)])
    elif opts.subcommand == 'webdiff':
        from nbdime.webapp import nbdiffweb
        return nbdiffweb.main(
            [opts.a, opts.b] +
            ['--%s' % name for name in diff_exclusives if getattr(opts, name)] +
            [i for l in [['--%s' % arg, str(getattr(opts, arg.replace('-', '_')))] for arg in web_args] for i in l]
            )
    elif opts.subcommand == 'config':
        opts.config_func(opts.scope)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
