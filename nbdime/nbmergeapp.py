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

import nbdime
import nbdime.log
from nbdime.merging import merge_notebooks
from nbdime.prettyprint import pretty_print_merge_decisions
from .merging import merge_notebooks

_description = ('Merge two Jupyter notebooks "local" and "remote" with a '
                'common ancestor "base".')


def main_merge(args):
    bfn = args.base
    lfn = args.local
    rfn = args.remote
    mfn = args.output

    for fn in (bfn, lfn, rfn):
        if not os.path.exists(fn):
            nbdime.log.error("Cannot find file '{}'".format(fn))
            return 1

    b = nbformat.read(bfn, as_version=4)
    l = nbformat.read(lfn, as_version=4)
    r = nbformat.read(rfn, as_version=4)

    merged, decisions = merge_notebooks(b, l, r, args)
    conflicted = [d for d in decisions if d.conflict]

    returncode = 1 if conflicted else 0

    if conflicted:
        nbdime.log.warning("Conflicts occured during merge operation.")
    else:
        nbdime.log.debug("Merge completed successfully with no unresolvable conflicts.")

    if args.decisions:
        # Print merge decisions (including unconflicted)
        out = io.StringIO()
        pretty_print_merge_decisions(b, decisions, out=out)
        nbdime.log.warning("Conflicts:\n%s", out.getvalue())
    elif mfn:
        # Write partial or fully completed merge to given foo.ipynb filename
        with io.open(mfn, "w", encoding="utf8") as mf:
            nbformat.write(merged, mfn)
        nbdime.log.info("Merge result written to %s" % mfn)
    else:
        # Write merged notebook to terminal
        nbformat.write(merged, sys.stdout)
    return returncode


def _build_arg_parser():
    """Creates an argument parser for the nbdiff command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    from .args import add_generic_args, add_diff_args, add_merge_args, add_filename_args
    add_generic_args(parser)
    add_diff_args(parser)
    add_merge_args(parser)
    add_filename_args(parser, ["base", "local", "remote"])

    parser.add_argument(
        '-o', '--output',
        default=None,
        help="if supplied, the merged notebook is written "
             "to this file. Otherwise it is printed to the "
             "terminal.")
    parser.add_argument(
        '-d', '--decisions',
        action="store_true",
        help="print a human-readable summary of conflicted "
             "merge decisions instead of merging the notebook.")

    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    nbdime.log.init_logging()
    arguments = _build_arg_parser().parse_args(args)
    nbdime.log.init_logging(level=arguments.log_level)
    return main_merge(arguments)


if __name__ == "__main__":
    sys.exit(main())
