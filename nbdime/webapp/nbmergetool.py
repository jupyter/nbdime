#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

from argparse import ArgumentParser
import nbformat
import os.path
import webbrowser
import logging
import threading

from ..args import (add_generic_args, add_diff_args,
    add_merge_args, add_web_args)
from .nbdimeserver import main as run_server


_logger = logging.getLogger(__name__)


# TODO: Tool server starts on random port (in optionally specified port range)
# TODO: Tool server is passed a (mandatory?) single-use access token, which is
#       used to authenticate the browser session.

def build_arg_parser():
    """
    Creates an argument parser for the merge tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'mergetool for Nbdime.'
    parser = ArgumentParser(description=description)
    add_generic_args(parser)
    add_diff_args(parser)
    add_merge_args(parser)
    add_web_args(parser, 8898)
    return parser


def browse(port):
    try:
        browser = webbrowser.get(None)
    except webbrowser.Error as e:
        _logger.warning('No web browser found: %s.', e)
        browser = None

    if browser:
        def launch_browser():
            browser.open("http://localhost:%s/mergetool" % port, new=2)
        threading.Thread(target=launch_browser).start()


def main():
    arguments = build_arg_parser().parse_args()
    port = arguments.port
    cwd = os.path.abspath(os.path.curdir)
    base = arguments.base
    local = arguments.local
    remote = arguments.remote
    merged = arguments.merged
    browse(port)
    run_server(port=port, cwd=cwd,
               mergetool_args=dict(base=base, local=local, remote=remote),
               outputfilename=merged)

if __name__ == "__main__":
    main()
