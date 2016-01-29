# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import nbformat
import json

from ._version import __version__
from .diffing.notebooks import diff_notebooks
from .prettyprint import pretty_print_notebook_diff


_usage = """\
Compute the difference between two Jupyter notebooks.

This is nbdiff from nbdime version {}.

Example usage:

  nbdiff before.ipynb after.ipynb patch.json
""".format(__version__)


def main_diff(afn, bfn, dfn=None):
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


def main():
    args = sys.argv[1:]
    if len(args) not in (2, 3):
        r = 1
    else:
        r = main_diff(*args)
    if r:
        print(_usage)
    sys.exit(r)
