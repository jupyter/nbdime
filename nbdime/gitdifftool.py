#!/usr/bin/env python
"""A git difftool plugin for notebooks.

Uses nbdime to display diffs of notebooks instead of plain text diffs of JSON.
Other files are displayed via `git diff`.

Enable in your global git config with:

    git-nbdifftool config --enable [--global]

Use with:

    git difftool [<commit> [<commit>]]
"""
import os
import sys
from subprocess import check_call, check_output, CalledProcessError

import nbdime.log
from .args import add_filename_args, add_generic_args
from .webapp import nbdifftool


def enable(global_=False, set_default=False):
    """Enable nbdime git difftool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    check_call(cmd + ['difftool.nbdime.cmd', 'git-nbdifftool diff "$LOCAL" "$REMOTE"'])
    if set_default:
        check_call(cmd + ['diff.guitool', 'nbdime'])

    # Common setting:
    check_call(cmd + ['difftool.prompt', 'false'])


def disable(global_=False, *args):
    """Disable nbdime git difftool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        tool = check_output(cmd + ['diff.guitool']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        pass
    else:
        if tool in ('nbdime', 'nbdimeweb'):
            try:
                check_call(cmd + ['--unset', 'diff.guitool'])
            except CalledProcessError:
                # already unset
                pass


def show_diff(before, after, opts):
    """Run the difftool

    If we are diffing a notebook, show the diff via nbdiff-web.
    Otherwise, call out to `git diff`.
    """
    # TODO: handle /dev/null (Windows equivalent?) for new or deleted files
    if before.endswith('.ipynb') or after.endswith('ipynb'):
        return nbdifftool.main_parsed(opts)
    else:
        # Never returns
        os.execvp('git', ['git', 'diff', before, after])


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('git-nbdifftool', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_generic_args(parser)
    subparsers = parser.add_subparsers(dest='subcommand')

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    nbdifftool.build_arg_parser(diff_parser)

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime via `git difftool`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
    )
    config.add_argument('--set-default', action='store_true', dest='set_default',
        help="set nbdime as default gui difftool"
    )
    enable_disable = config.add_mutually_exclusive_group(required=True)
    enable_disable.add_argument('--enable', action='store_const',
        dest='config_func', const=enable,
        help="enable nbdime difftool via git config"
    )
    enable_disable.add_argument('--disable', action='store_const',
        dest='config_func', const=disable,
        help="disable nbdime difftool via git config"
    )
    opts = parser.parse_args(args)
    nbdime.log.init_logging(level=opts.log_level)
    if opts.subcommand == 'diff':
        return show_diff(opts.local, opts.remote, opts)
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_, opts.set_default)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
