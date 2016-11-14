# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import io
import os
import sys
import argparse
from pprint import pprint

import nbformat
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
            print("Cannot find file '{}'".format(fn))
            return 1

    b = nbformat.read(bfn, as_version=4)
    l = nbformat.read(lfn, as_version=4)
    r = nbformat.read(rfn, as_version=4)

    m, decisions = merge_notebooks(b, l, r, args)
    conflicted = [d for d in decisions if d.conflict]

    returncode = 1 if conflicted else 0

    if conflicted:
        print("Conflicts occured during merge operation.")
    else:
        print("Merge completed successfully with no unresolvable conflicts.")

    if mfn:
        # Add remaining conflicts to metadata
        if conflicted:
            m["metadata"]["nbdime-conflicts"] = conflicted
        # Write partial or fully completed merge to given foo.ipynb filename
        with io.open(mfn, "wb") as mf:
            # FIXME: We currently write this way as git needs \n line endings,
            # when used as merge driver. However, we should write using OS
            # line endings otherwise.
            nb = nbformat.from_dict(m)
            s = nbformat.writes(nb) + u'\n'
            mf.write(s.encode())
    else:
        # FIXME: Display conflicts in a useful way
        if conflicted:
            print("Conflicts:")
            pprint(conflicted)
        print("Merge result:")
        pprint(m)
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

    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = _build_arg_parser().parse_args(args)
    return main_merge(arguments)


if __name__ == "__main__":
    import nbdime.log
    nbdime.log.init_logging()
    main()
