# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import io
import os
import sys
import argparse
import json

from six import string_types

import nbdime
from nbdime.diffing.notebooks import diff_notebooks
from nbdime.prettyprint import pretty_print_notebook_diff
from nbdime.args import (
    add_generic_args, add_diff_args, process_diff_args)
from nbdime.utils import EXPLICIT_MISSING_FILE, read_notebook, setup_std_streams
from .gitfiles import changed_notebooks, is_valid_gitref


_description = "Compute the difference between two Jupyter notebooks."


def main_diff(args):
    # Get input notebooks:
    afn = args.base
    bfn = args.remote
    dfn = args.out

    process_diff_args(args)

    for fn in (afn, bfn):
        if isinstance(fn, string_types) and not os.path.exists(fn) and fn != EXPLICIT_MISSING_FILE:
            print("Missing file {}".format(fn))
            return 1
    # Both files cannot be missing
    assert not (afn == EXPLICIT_MISSING_FILE and bfn == EXPLICIT_MISSING_FILE)

    a = read_notebook(afn, on_null='empty')
    b = read_notebook(bfn, on_null='empty')

    # Perform actual diff:
    d = diff_notebooks(a, b)

    # Output diff:
    if dfn:
        with open(dfn, "w") as df:
            # Compact version:
            #json.dump(d, df)
            # Verbose version:
            json.dump(d, df, indent=2, separators=(",", ": "))
    else:
        # This printer is to keep the unit tests passing,
        # some tests capture output with capsys which doesn't
        # pick up on sys.stdout.write()
        class Printer:
            def write(self, text):
                print(text, end="")
        if not isinstance(afn, string_types):
            afn = afn.name
        if not isinstance(bfn, string_types):
            bfn = bfn.name
        pretty_print_notebook_diff(afn, bfn, a, d, Printer())

    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbdiff command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    add_generic_args(parser)
    add_diff_args(parser)
    parser.add_argument(
        "base", help="The base notebook filename OR base git-revision.",
        nargs='?', default='HEAD',
    )
    parser.add_argument(
        "remote", help="The remote modified notebook filename OR remote git-revision.",
        nargs='?', default=None,
    )

    parser.add_argument(
        '--out',
        default=None,
        help="if supplied, the diff is written to this file. "
             "Otherwise it is printed to the terminal.")

    return parser


def is_gitref(candidate):
    return is_valid_gitref(candidate) and (candidate is None or not os.path.exists(candidate))


def handle_gitrefs(base, remote, arguments):
    status = 0
    for fbase, fremote in changed_notebooks(base, remote):
        arguments.base = fbase
        arguments.remote = fremote
        status = main_diff(arguments)
        if status != 0:
            return status
    return status


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    setup_std_streams()
    arguments = _build_arg_parser().parse_args(args)
    base = arguments.base
    remote = arguments.remote
    nbdime.log.init_logging(level=arguments.log_level)
    if is_gitref(base) and is_gitref(remote):
        # We are asked to do a diff of git revisions:
        return handle_gitrefs(base, remote, arguments)
    return main_diff(arguments)


if __name__ == "__main__":
    sys.exit(main())
