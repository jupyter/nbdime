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

from .diffing.notebooks import diff_notebooks
from .prettyprint import pretty_print_notebook_diff
from .args import add_generic_args, add_diff_args, add_filename_args


_description = "Compute the difference between two Jupyter notebooks."


def main_diff(args):
    afn = args.base
    bfn = args.remote
    dfn = args.output

    for fn in (afn, bfn):
        if not os.path.exists(fn):
            print("Missing file {}".format(fn))
            return 1

    a = nbformat.read(afn, as_version=4)
    b = nbformat.read(bfn, as_version=4)

    d = diff_notebooks(a, b)

    verbose = True
    if verbose:
        pretty_print_notebook_diff(afn, bfn, a, d)

    if dfn:
        with io.open(dfn, "w", encoding="utf8") as df:
            # Compact version:
            #json.dump(d, df)
            # Verbose version:
            json.dump(d, df, indent=2, separators=(",", ": "))
    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbdiff command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    add_generic_args(parser)
    add_diff_args(parser)
    add_filename_args(parser, ["base", "remote"])

    parser.add_argument(
        '-o', '--output',
        default=None,
        help="if supplied, the diff is written to this file. "
             "Otherwise it is printed to the terminal.")

    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if sys.platform.startswith('win'):
        import colorama
        colorama.init()
    arguments = _build_arg_parser().parse_args(args)
    return main_diff(arguments)


if __name__ == "__main__":
    import nbdime.log
    nbdime.log.init_logging()
    main()
