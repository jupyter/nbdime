#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser
import warnings

from .nbdimeserver import main_server as run_server
from .webutil import browse as browse_util
from ..args import add_generic_args, add_web_args, add_diff_args, add_filename_args
import nbdime.log


def build_arg_parser():
    """
    Creates an argument parser for the diff tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'Difftool for Nbdime.'
    parser = ArgumentParser(
        description=description,
        add_help=True
        )
    add_generic_args(parser)
    add_web_args(parser, 0)
    add_diff_args(parser)
    add_filename_args(parser, ["base", "remote"])
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


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = build_arg_parser().parse_args(args)
    nbdime.log.init_logging(level=arguments.log_level)
    port = arguments.port
    ip = arguments.ip
    base_url = arguments.base_url
    cwd = arguments.workdirectory
    base = arguments.base
    remote = arguments.remote
    browsername = arguments.browser
    return run_server(
        port=port, cwd=cwd, ip=ip,
        closable=True,
        base_url=base_url,
        on_port=lambda port: browse_util(
            port=port,
            base_url=base_url,
            browsername=browsername,
            rel_url='diff',
            ip=ip,
            base=base, remote=remote))


if __name__ == "__main__":
    sys.exit(main())
