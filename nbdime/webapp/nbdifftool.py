#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

from argparse import ArgumentParser
import os.path
import webbrowser
import logging
import threading

from ..args import (add_generic_args, add_diff_args,
    add_web_args)
from .nbdimeserver import main as run_server


_logger = logging.getLogger(__name__)


# TODO: Tool server is passed a (mandatory?) single-use access token, which is
#       used to authenticate the browser session.

def build_arg_parser():
    """
    Creates an argument parser for the diff tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'difftool for Nbdime.'
    parser = ArgumentParser(description=description)
    add_generic_args(parser)
    add_web_args(parser, 0)
    add_diff_args(parser)
    return parser


def browse(port):
    try:
        browser = webbrowser.get(None)
    except webbrowser.Error as e:
        _logger.warning('No web browser found: %s.', e)
        browser = None

    if browser:
        def launch_browser():
            browser.open("http://127.0.0.1:%s/difftool" % port, new=2)
        threading.Thread(target=launch_browser).start()


def main():
    arguments = build_arg_parser().parse_args()
    port = arguments.port
    cwd = arguments.workdirectory
    local = arguments.local
    remote = arguments.remote
    browse(port)
    run_server(port=port, cwd=cwd,
               difftool_args=dict(base=local, remote=remote))

if __name__ == "__main__":
    main()
