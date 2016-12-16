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

def build_arg_parser(parser=None):
    """
    Creates an argument parser for the merge tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'mergetool for Nbdime.'
    if parser is None:
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

    url = "http://127.0.0.1:%s/mergetool" % port
    nbdime.log.info("URL: " + url)
    if browser:
        def launch_browser():
            browser.open(url, new=2)
        threading.Thread(target=launch_browser).start()


def main_parsed(opts):
    """Main function called after parsing CLI options

    Called by both main here and gitmergetool
    """
    nbdime.log.init_logging(level=opts.log_level)
    port = opts.port
    cwd = opts.workdirectory
    base = opts.base
    local = opts.local
    remote = opts.remote
    merged = opts.merged
    browsername = opts.browser
    return run_server(port=port, cwd=cwd,
                      closable=True,
                      mergetool_args=dict(base=base, local=local, remote=remote),
                      outputfilename=merged,
                      on_port=lambda port: browse(port, browsername))


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = build_arg_parser().parse_args(args)
    return main_parsed(opts)



if __name__ == "__main__":
    sys.exit(main())
