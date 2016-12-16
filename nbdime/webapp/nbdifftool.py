#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import sys
from argparse import ArgumentParser
import webbrowser
import logging
import threading

from ..args import add_generic_args, add_diff_args
from ..args import add_web_args, add_filename_args
from .nbdimeserver import main_server as run_server
import nbdime.log


_logger = logging.getLogger(__name__)


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


def browse(port, browsername):
    try:
        browser = webbrowser.get(browsername)
    except webbrowser.Error as e:
        _logger.warning('No web browser found: %s.', e)
        browser = None

    url = "http://127.0.0.1:%s/difftool" % port
    nbdime.log.info("URL: " + url)
    if browser:
        def launch_browser():
            browser.open(url, new=2)
        threading.Thread(target=launch_browser).start()


def main_parsed(opts):
    """Main function called after parsing CLI options

    Called by both main here and gitdifftool
    """
    nbdime.log.init_logging(level=opts.log_level)
    port = opts.port
    cwd = opts.workdirectory
    base = opts.local
    remote = opts.remote
    browsername = opts.browser
    return run_server(
        port=port, cwd=cwd,
        closable=True,
        difftool_args=dict(base=base, remote=remote),
        on_port=lambda port: browse(port, browsername))

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = build_arg_parser().parse_args(args)
    return main_parsed(opts)



if __name__ == "__main__":
    sys.exit(main())
