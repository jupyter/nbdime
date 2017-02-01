#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser

from ..args import add_generic_args, add_diff_args
from ..args import add_merge_args, add_web_args, add_filename_args
from .nbdimeserver import main_server as run_server
from .webutil import browse
import nbdime.log


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
        '-o', '--output',
        default=None,
        help="if supplied, the merged notebook is written "
             "to this file. Otherwise it cannot be saved.")
    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = build_arg_parser().parse_args(args)
    nbdime.log.init_logging(level=arguments.log_level)
    port = arguments.port
    ip = arguments.ip
    cwd = arguments.workdirectory
    base = arguments.base
    local = arguments.local
    remote = arguments.remote
    output = arguments.output
    browsername = arguments.browser
    return run_server(
        port=port, cwd=cwd, ip=ip,
        closable=True,
        outputfilename=output,
        on_port=lambda port: browse(
            ip, port, browsername, 'merge',
            base=base, local=local, remote=remote))


if __name__ == "__main__":
    sys.exit(main())
