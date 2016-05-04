# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import argparse
import json
import nbformat
from ._version import __version__
from .patching import patch_notebook
from .diff_format import to_diffentry_dicts

_description = "Apply patch from nbdiff to a Jupyter notebook."


def main_patch(args):
    bfn = args.base
    dfn = args.patch
    afn = args.output

    for fn in (bfn, dfn):
        if not os.path.exists(fn):
            print("Missing file {}".format(fn))
            return 1

    before = nbformat.read(bfn, as_version=4)
    with open(dfn) as df:
        d = json.load(df)
    d = to_diffentry_dicts(d)

    # TODO: Split lines here? Must be consistent with the diff for patch_notebook to work correctly!?
    #before = split_lines(before)

    after = patch_notebook(before, d)

    if afn:
        nbformat.write(after, afn)
    else:
        print(after)

    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbpatch command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    from .nbdiffapp import add_generic_args
    add_generic_args(parser)

    parser.add_argument('base',
                        help="The base notebook filename.")
    parser.add_argument('patch',
                        help="The patch filename, output from nbdiff.")
    return parser


def main():
    args = _build_arg_parser().parse_args()
    r = main_patch(args)
    sys.exit(r)
