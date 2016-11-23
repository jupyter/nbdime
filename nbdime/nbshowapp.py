# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import io
import os
import sys
import argparse
import nbformat
import json

import nbdime
from nbdime.prettyprint import pretty_print_notebook
from nbdime.args import add_generic_args, add_filename_args


_description = "Show a Jupyter notebook in terminal."


def main_show(args):
    afn = args.base

    for fn in (afn,):
        if not os.path.exists(fn):
            print("Missing file {}".format(fn))
            return 1

    a = nbformat.read(afn, as_version=4)

    # This printer is to keep the unit tests passing,
    # some tests capture output with capsys which doesn't
    # pick up on sys.stdout.write()
    class Printer:
        def write(self, text):
            print(text, end="")
    pretty_print_notebook(a, Printer())

    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbshow command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    add_generic_args(parser)
    add_filename_args(parser, ["base"])

    # TODO: Options to show only important things: --compact, --source-only

    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if sys.platform.startswith('win'):
        import colorama
        colorama.init()
    arguments = _build_arg_parser().parse_args(args)
    nbdime.log.set_nbdime_log_level(arguments.log_level)
    return main_show(arguments)


if __name__ == "__main__":
    nbdime.log.init_logging()
    main()
