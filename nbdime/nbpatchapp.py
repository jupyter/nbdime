# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys
import json
import io

import nbformat

from .args import ConfigBackedParser
from .patching import patch_notebook
from .diff_utils import to_diffentry_dicts
from .utils import EXPLICIT_MISSING_FILE, read_notebook, setup_std_streams
from .prettyprint import pretty_print_notebook, PrettyPrintConfig


_description = "Apply patch from nbdiff to a Jupyter notebook."


def main_patch(args):
    base_filename = args.base
    patch_filename = args.patch
    output_filename = args.output

    for fn in (base_filename, patch_filename):
        if not os.path.exists(fn) and fn != EXPLICIT_MISSING_FILE:
            print("Missing file {}".format(fn))
            return 1

    before = read_notebook(base_filename, on_null='empty')
    with io.open(patch_filename, encoding="utf8") as patch_file:
        diff = json.load(patch_file)
    diff = to_diffentry_dicts(diff)

    after = patch_notebook(before, diff)

    if output_filename:
        nbformat.write(after, output_filename)
    else:
        try:
            nbformat.validate(after, version=4)
        except nbformat.ValidationError:
            print("Patch result is not a valid notebook, printing as JSON:")
            json.dump(after, sys.stdout)
        else:
            # This printer is to keep the unit tests passing,
            # some tests capture output with capsys which doesn't
            # pick up on sys.stdout.write()
            class Printer:
                def write(self, text):
                    print(text, end="")

            config = PrettyPrintConfig(out=Printer())

            pretty_print_notebook(after, config=config)

    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbpatch command."""
    parser = ConfigBackedParser(
        description=_description,
        add_help=True,
        )
    from .args import add_generic_args, add_filename_args
    add_generic_args(parser)
    add_filename_args(parser, ["base", "patch"])
    parser.add_argument(
        '-o', '--output',
        default=None,
        help="if supplied, the patched notebook is written "
             "to this file. Otherwise it is printed to the "
             "terminal.")
    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    setup_std_streams()
    arguments = _build_arg_parser().parse_args(args)
    return main_patch(arguments)


if __name__ == "__main__":
    sys.exit(main())
