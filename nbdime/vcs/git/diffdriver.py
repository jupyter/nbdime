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



import io
import os
import sys
from subprocess import check_call, CalledProcessError

from nbdime.args import (
    add_git_config_subcommand, add_generic_args, add_diff_args, add_web_args,
    add_git_diff_driver_args, add_diff_cli_args, ConfigBackedParser,
    add_prettyprint_args
    )
from nbdime.utils import locate_gitattributes, ensure_dir_exists, setup_std_streams
from .filter_integration import apply_possible_filter

def enable(scope=None):
    """Enable nbdime git diff driver"""
    cmd = ['git', 'config']
    if scope:
        cmd.append('--%s' % scope)

    try:
        check_call(cmd + ['diff.jupyternotebook.command', 'git-nbdiffdriver diff'])
    except CalledProcessError:
        return   # Not in git repository
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


def _build_arg_parser():
    import argparse
    parser = ConfigBackedParser('git-nbdiffdriver',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_generic_args(parser)

    subparsers = parser.add_subparsers(dest='subcommand')

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    add_git_diff_driver_args(diff_parser)
    add_diff_args(diff_parser)
    add_diff_cli_args(diff_parser)
    add_prettyprint_args(diff_parser)

    webdiff_parser = subparsers.add_parser('webdiff',
        description="The actual entrypoint for the webdiff tool. Git will call this."
    )
    add_git_diff_driver_args(webdiff_parser)
    add_diff_args(webdiff_parser)
    add_web_args(webdiff_parser, 0)

    # TODO: From git docs: "For a path that is unmerged, GIT_EXTERNAL_DIFF is called with 1 parameter, <path>."
    add_git_config_subcommand(subparsers,
        enable, disable,
        subparser_help="Configure git to use nbdime for notebooks in `git diff`",
        enable_help="enable nbdime diff driver via git config",
        disable_help="disable nbdime diff driver via git config")

    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    setup_std_streams()
    parser = _build_arg_parser()
    opts = parser.parse_args(args)

    if opts.subcommand == 'diff':
        from nbdime import nbdiffapp
        if opts.use_filter and opts.remote:
            opts.remote = apply_possible_filter(opts.path, opts.remote)
        return nbdiffapp.main_diff(opts)
    elif opts.subcommand == 'webdiff':
        from nbdime.webapp import nbdiffweb
        if opts.use_filter and opts.remote:
            opts.remote = apply_possible_filter(opts.path, opts.remote)
        return nbdiffweb.main_diff(opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.scope)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
