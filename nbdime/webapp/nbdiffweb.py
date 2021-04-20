#!/usr/bin/env python
# -*- coding:utf-8 -*-




import sys

import warnings

from .nbdimeserver import main_server as run_server
from .webutil import browse as browse_util
from ..args import (
    ConfigBackedParser,
    add_generic_args, add_web_args, add_diff_args,
    args_for_server, args_for_browse, process_diff_flags,
    resolve_diff_args)
from ..gitfiles import changed_notebooks, is_gitref


def build_arg_parser():
    """
    Creates an argument parser for the diff tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'Difftool for Nbdime.'
    parser = ConfigBackedParser(
        description=description,
        add_help=True
        )
    add_generic_args(parser)
    add_web_args(parser, 0)
    add_diff_args(parser)
    parser.add_argument(
        "base", help="The base notebook filename OR base git-revision.",
        nargs='?', default='HEAD',
    )
    parser.add_argument(
        "remote", help="The remote modified notebook filename OR remote git-revision.",
        nargs='?', default=None,
    )
    parser.add_argument(
        "paths", help="Filter diffs for git-revisions based on path",
        nargs='*', default=None,
    )
    return parser


def browse(port, base, remote, browser):
    browse_util(port=port,
                browsername=browser,
                rel_url='diff',
                base=base,
                remote=remote)
    warnings.warn(
        'This function is deprecated. '
        'Use nbdime.webapp.webutil.browse() instead.',
        DeprecationWarning)


def handle_gitrefs(base, remote, path, arguments):
    status = 0
    for fbase, fremote in changed_notebooks(base, remote, path):
        status = run_server(
            difftool_args=dict(base=fbase, remote=fremote),
            on_port=lambda port: browse_util(
                port=port,
                rel_url='difftool',
                **args_for_browse(arguments)),
            **args_for_server(arguments))
        if status != 0:
            # Short-circuit for errors along the way
            return status
    return status


def main_diff(opts):
    process_diff_flags(opts)
    base, remote, path = resolve_diff_args(opts)
    if is_gitref(base) and is_gitref(remote):
        # We are asked to do a gui for git diff
        return handle_gitrefs(base, remote, path, opts)
    return run_server(
        on_port=lambda port: browse_util(
            port=port,
            rel_url='diff',
            base=base, remote=remote,
            **args_for_browse(opts)),
        **args_for_server(opts))


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = build_arg_parser().parse_args(args)
    return main_diff(opts)


if __name__ == "__main__":
    sys.exit(main())
