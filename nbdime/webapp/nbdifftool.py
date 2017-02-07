#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser

from ..args import add_generic_args, add_diff_args
from ..args import add_web_args, add_filename_args
from .nbdimeserver import main_server as run_server
from .webutil import browse
import nbdime.log


# TODO: Tool server is passed a (mandatory?) single-use access token, which is
#       used to authenticate the browser session.

def build_arg_parser(parser=None):
    """
    Creates an argument parser for the diff tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'difftool for nbdime.'
    if parser is None:
        parser = ArgumentParser(
            description=description,
            add_help=True
            )
    add_generic_args(parser)
    add_web_args(parser, 0)
    add_diff_args(parser)
    add_filename_args(parser, ["local", "remote"])
    return parser


def main_parsed(opts):
    """Main function called after parsing CLI options

    Called by both main here and gitdifftool
    """
    nbdime.log.init_logging(level=opts.log_level)
    port = opts.port
    ip = opts.ip
    cwd = opts.workdirectory
    base = opts.local
    remote = opts.remote
    browsername = opts.browser
    return run_server(
        port=port, cwd=cwd, ip=ip,
        closable=True,
        difftool_args=dict(base=base, remote=remote),
        on_port=lambda port: browse(
            port=port,
            browsername=browsername,
            rel_url='difftool',
            ip=ip))


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = build_arg_parser().parse_args(args)
    return main_parsed(opts)


if __name__ == "__main__":
    sys.exit(main())
