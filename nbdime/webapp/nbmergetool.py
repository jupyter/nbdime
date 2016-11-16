#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser
import webbrowser
import logging
import threading

from ..args import add_generic_args, add_filename_args
from ..args import add_diff_args, add_merge_args, add_web_args
from .nbdimeserver import main_server as run_server
import nbdime.log


_logger = logging.getLogger(__name__)


# TODO: Tool server is passed a (mandatory?) single-use access token, which is
#       used to authenticate the browser session.

def build_arg_parser():
    """
    Creates an argument parser for the merge tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'mergetool for Nbdime.'
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
    add_filename_args(parser, ["base", "local", "remote", "merged"])
    return parser


def browse(port, browsername):
    try:
        browser = webbrowser.get(browsername)
    except webbrowser.Error as e:
        _logger.warning('No web browser found: %s.', e)
        browser = None

    if browser:
        def launch_browser():
            browser.open("http://127.0.0.1:%s/mergetool" % port, new=2)
        threading.Thread(target=launch_browser).start()


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = build_arg_parser().parse_args()
    nbdime.log.set_nbdime_log_level(arguments.loglevel)
    port = arguments.port
    cwd = arguments.workdirectory
    base = arguments.base
    local = arguments.local
    remote = arguments.remote
    merged = arguments.merged
    browsername = arguments.browser
    return run_server(port=port, cwd=cwd,
                      closable=True,
                      mergetool_args=dict(base=base, local=local, remote=remote),
                      outputfilename=merged,
                      on_port=lambda port: browse(port, browsername))


if __name__ == "__main__":
    nbdime.log.init_logging()
    main()
