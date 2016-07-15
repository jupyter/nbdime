# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import json
import os
import sys
import argparse
from pprint import pprint

import nbformat
from ._version import __version__
from .merging import merge_notebooks

_description = 'Merge two Jupyter notebooks "local" and "remote" with a common ancestor "base".'


def main_merge(args):
    bfn = args.base
    lfn = args.local
    rfn = args.remote
    mfn = args.output

    for fn in (bfn, lfn, rfn):
        if not os.path.exists(fn):
            print("Cannot find file '{}'".format(fn))
            print(_usage)
            return 1

    b = nbformat.read(bfn, as_version=4)
    l = nbformat.read(lfn, as_version=4)
    r = nbformat.read(rfn, as_version=4)

    # TODO: Split lines here?
    #b = split_lines(b)
    #l = split_lines(l)
    #r = split_lines(r)

    m, lc, rc = merge_notebooks(b, l, r, args)

    if lc or rc:
        print("Conflicts occured during merge operation.")
    else:
        print("Merge completed successfully with no unresolvable conflicts.")

    if mfn:
        if lc or rc:
            # Write partial merge and conflicts to a foo.ipynb-merge file
            result = {
                "merged": m,
                "local_conflicts": lc,
                "remote_conflicts": rc
                }
            with open(mfn+"-merge", "w") as mf:
                json.dump(result, mf)
        else:
            # Write fully completed merge to given foo.ipynb filename
            with open(mfn, "w") as mf:
                nbformat.write(m, mf)
    else:
        # FIXME: Display conflicts in a useful way
        if lc or rc:
            print("Local conflicts:")
            pprint(lc)
            print("Remote conflicts:")
            pprint(rc)
    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbdiff command."""
    parser = argparse.ArgumentParser(
        description=_description,
        add_help=True,
        )
    from .nbdiffapp import add_generic_args, add_webgui_args, add_diff_args
    add_generic_args(parser)
    #add_webgui_args(parser)
    add_diff_args(parser)

    # TODO: Define sensible strategy variables and implement
    from .merging.notebooks import generic_conflict_strategies
    parser.add_argument('-s', '--strategy',
                        default="mergetool", choices=generic_conflict_strategies,
                        help="Specify the merge strategy to use.")
    #parser.add_argument('-m', '--merge-strategy',
    #                    default="default", choices=("foo", "bar"),
    #                    help="Specify the merge strategy to use.")
    parser.add_argument('-i', '--ignore-transients',
                        action="store_true",
                        default=False,
                        help="Allow automatic deletion of transient data to resolve conflicts (output, execution count).")

    parser.add_argument('base',
                        help="The base notebook filename.")
    parser.add_argument('local',
                        help="The local modified notebook filename.")
    parser.add_argument('remote',
                        help="The remote modified notebook filename.")
    return parser


def main():
    args = _build_arg_parser().parse_args()
    r = main_merge(args)
    sys.exit(r)
