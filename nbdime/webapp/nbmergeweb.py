#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser
import os.path
import webbrowser
import logging
import threading
from tornado.httputil import url_concat

from ..args import (add_generic_args, add_diff_args,
    add_merge_args, add_web_args)
from .nbdimeserver import main as run_server


_logger = logging.getLogger(__name__)


def build_arg_parser():
    """
    Creates an argument parser for the diff tool, that also lets the
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
    parser.add_argument(
        '-o', '--output',
        default=None,
        help="if supplied, the merged notebook is written "
             "to this file. Otherwise it cannot be saved.")
    return parser


def browse(port, base, local, remote):
    try:
        browser = webbrowser.get(None)
    except webbrowser.Error as e:
        _logger.warning('No web browser found: %s.', e)
        browser = None

    if browser:
        b = lambda: browser.open(
            url_concat("http://127.0.0.1:%s/diff" % port,
                       dict(base=base, local=local,
                            remote=remote)),
            new=2)
        threading.Thread(target=b).start()


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = build_arg_parser().parse_args(args)
    port = arguments.port
    cwd = arguments.workdirectory
    base = arguments.base
    local = arguments.local
    remote = arguments.remote
    browse(port, base, local, remote)
    return run_server(port=port, cwd=cwd)
