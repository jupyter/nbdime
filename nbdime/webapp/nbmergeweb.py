#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser

from ..args import (add_generic_args, add_diff_args, add_merge_args,
    add_web_args, add_filename_args, args_for_server, args_for_browse,
    process_diff_flags)
from .nbdimeserver import main_server as run_server
from .webutil import browse


def build_arg_parser():
    """
    Creates an argument parser for the merge tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'Mergetool for Nbdime.'
    parser = ArgumentParser(
        description=description,
        add_help=True
        )
    add_generic_args(parser)
    add_diff_args(parser)
    add_merge_args(parser)
    add_web_args(parser, 0)
    add_filename_args(parser, ["base", "local", "remote"])
    parser.add_argument(
        '--out',
        default=None,
        help="if supplied, the merged notebook is written "
             "to this file. Otherwise it cannot be saved.")
    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = build_arg_parser().parse_args(args)
    process_diff_flags(arguments)
    base = arguments.base
    local = arguments.local
    remote = arguments.remote
    output = arguments.out
    return run_server(
        closable=True,
        outputfilename=output,
        on_port=lambda port: browse(
            port=port,
            rel_url='merge',
            base=base, local=local, remote=remote,
            **args_for_browse(arguments)),
        **args_for_server(arguments))


if __name__ == "__main__":
    sys.exit(main())
