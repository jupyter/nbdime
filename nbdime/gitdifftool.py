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

from . import nbdiffapp

def enable(global_=False):
    """Enable nbdime git difftool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    check_call(cmd + ['difftool.nbdime.cmd', 'git-nbdifftool diff "$LOCAL" "$REMOTE"'])
    try:
        previous = check_output(cmd + ['diff.tool']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        previous = None
    else:
        if previous != 'nbdime':
            check_call(cmd + ['difftool.nbdime.previous', previous])
    check_call(cmd + ['diff.tool', 'nbdime'])

    check_call(cmd + ['difftool.nbdimeweb.cmd', 'git-nbwebdifftool "$LOCAL" "$REMOTE"'])
    try:
        previous = check_output(cmd + ['diff.guitool']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        previous = None
    else:
        if previous != 'nbdime':
            check_call(cmd + ['difftool.nbdimeweb.previous', previous])
    check_call(cmd + ['diff.guitool', 'nbdimeweb'])

    # Common setting:
    check_call(cmd + ['difftool.prompt', 'false'])


def disable(global_=False):
    """Disable nbdime git difftool"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        previous = check_output(cmd + ['difftool.nbdime.previous']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        check_call(cmd + ['--unset', 'diff.tool'])
    else:
        check_call(cmd + ['diff.tool', previous])
    try:
        previous_gui = check_output(cmd + ['difftool.nbdime.previous_gui']).decode('utf8', 'replace').strip()
    except CalledProcessError:
        check_call(cmd + ['--unset', 'diff.guitool'])
    else:
        check_call(cmd + ['diff.guitool', previous_gui])


def show_diff(before, after):
    """Run the difftool

    If we are diffing a notebook, show the diff via nbdiff.
    Otherwise, call out to `git diff`.
    """
    # TODO: handle /dev/null (Windows equivalent?) for new or deleted files
    if before.endswith('.ipynb') or after.endswith('ipynb'):
        nbdiffapp.main([before, after])
    else:
        os.execvp('git', ['git', 'diff', before, after])


def main():
    import argparse
    parser = argparse.ArgumentParser('git-nbdifftool', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    diff_parser.add_argument('local')
    diff_parser.add_argument('remote')

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime via `git difftool`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
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
    opts = parser.parse_args()
    if opts.subcommand == 'diff':
        show_diff(opts.local, opts.remote)
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
