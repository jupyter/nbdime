# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import argparse
import nbformat
import json

from ._version import __version__
from .diffing.notebooks import diff_notebooks
from .prettyprint import pretty_print_notebook_diff


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

    # TODO: Split lines here?
    #a = split_lines(a)
    #b = split_lines(b)

    d = diff_notebooks(a, b)

    verbose = True
    if verbose:
        pretty_print_notebook_diff(afn, bfn, a, d)

    if dfn:
        with open(dfn, "w") as df:
            # Compact version:
            #json.dump(d, df)
            # Verbose version:
            json.dump(d, df, indent=2, separators=(",", ": "))
    return 0


# TODO: Reuse these add_*_args functions across the apps
def add_generic_args(parser):
    parser.add_argument('--version',
                        action="version",
                        version="%(prog)s " + __version__)
    parser.add_argument('-o', '--output',
                        default=None,
                        help="the output filename.")
    if 0:  # TODO: Use verbose and quiet across nbdime and enable these:
        qv_group = parser.add_mutually_exclusive_group()
        qv_group.add_argument('-v', '--verbose',
                             default=False,
                             action="store_true",
                             help="increase verbosity of console output.")
        qv_group.add_argument('-q', '--quiet',
                              default=False,
                              action="store_true",
                              help="silence console output.")

def add_webgui_args(parser):
    parser.add_argument('-p', '--port',
                        default=8888,
                        type=int,
                        help="specify the port you want the server "
                             "to run on. Default is 8888.")
    cwd = os.path.abspath(os.path.curdir)
    parser.add_argument('-w', '--workdirectory',
                        default=cwd,  # TODO: Are there any security implications of doing this?
                        help="specify the working directory you want "
                             "the server to run from. Default is the "
                             "actual cwd at program start.")

def add_diff_args(parser):
    # TODO: Add diff strategy options that are reusable for the merge command here

    # TODO: Define sensible strategy variables and implement
    #parser.add_argument('-d', '--diff-strategy',
    #                    default="default", choices=("foo", "bar"),
    #                    help="specify the diff strategy to use.")
    pass


def _build_arg_parser():
    """Creates an argument parser for the nbdiff command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    add_generic_args(parser)
    #add_webgui_args(parser)
    add_diff_args(parser)

    parser.add_argument('base',
                        help="the base notebook file.")
    parser.add_argument('remote',
                        help="the modified notebook file.")
    return parser


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)
    r = main_diff(args)
    sys.exit(r)
