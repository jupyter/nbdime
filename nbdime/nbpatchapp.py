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
    base_filename = args.base
    path_filename = args.patch
    output_filename = args.output

    for fn in (base_filename, path_filename):
        if not os.path.exists(fn):
            print("Missing file {}".format(fn))
            return 1

    before = nbformat.read(base_filename, as_version=4)
    with open(path_filename) as patch_file:
        diff = json.load(patch_file)
    diff = to_diffentry_dicts(diff)

    after = patch_notebook(before, diff)

    if output_filename:
        nbformat.write(after, output_filename)
    else:
        print(after)

    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbpatch command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    from .args import add_generic_args
    add_generic_args(parser)

    parser.add_argument(
        'base',
        help="The base notebook filename.")
    parser.add_argument(
        'patch',
        help="The patch filename, output from nbdiff.")
    parser.add_argument(
        '-o', '--output',
        default=None,
        help="if supplied, the patched notebook is written "
             "to this file. Otherwise it is printed to the "
             "terminal.")
    return parser


def main():
    args = _build_arg_parser().parse_args()
    r = main_patch(args)
    sys.exit(r)
