"""Utilities for merging notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import os
import sys
import nbformat
from ._version import __version__
from .merging import merge_notebooks


_usage = """\
Merge two Jupyter notebooks "local" and "remote" with a common ancestor "base".

This is nbmerge from nbdime version {}.

Example usage:

  jupyter nbmerge base.ipynb local.ipynb remote.ipynb merged.ipynb
""".format(__version__)


def main_merge(bfn, lfn, rfn, mfn):
    for fn in (bfn, lfn, rfn):
        if not os.path.exists(fn):
            print("Cannot find file '{}'".format(fn))
            print(_usage)
            return 1

    b = nbformat.read(bfn, as_version=4)
    l = nbformat.read(lfn, as_version=4)
    r = nbformat.read(rfn, as_version=4)

    m = merge_notebooks(b, l, r)

    verbose = True
    if verbose:
        print(m)

    nbformat.write(mfn, m)
    return 0


def main():
    args = sys.argv[1:]
    if len(args) != 4:
        r = 1
    else:
        r = main_merge(*args)
    if r:
        print(_usage)
    sys.exit(r)
