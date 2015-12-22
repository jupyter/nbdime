"""Utilities for diffing notebooks"""

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
from .dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE


# TODO: Improve and make a more reusable utility.
import pprint
def present_diff(d, indent=0):
    "Pretty-print a nbdime diff."
    indsep = " "*4
    ind = indsep*indent
    ind2 = indsep*(indent+1)

    pp = []
    for e in d:
        action = e[0]
        key = e[1]
        if action == DELETE:
            pp.append("{}{} {}".format(ind, action, key))
        elif action in (INSERT, REPLACE):
            lines = pprint.pformat(e[2]).splitlines()
            pp.append("{}{} {}".format(ind, action, key))
            pp.extend(ind2+line for line in lines)
        elif action == PATCH:
            lines = present_diff(e[2]).splitlines()
            pp.append("{}{} {}".format(ind, action, key))
            pp.extend(ind2+line for line in lines)
        elif action == SEQDELETE:
            pp.append("{}{} {}-{}".format(ind, action, key, e[2]))
        elif action == SEQINSERT:
            lines = pprint.pformat(e[2]).splitlines()
            pp.append("{}{} {}-{}".format(ind, action, key, len(e[2])))
            pp.extend(ind2+line for line in lines)
        else:
            error("Can't print {}".format(e[0]))
    return "\n".join(pp)


def pretty_print_notebook_diff(d):
    assert isinstance(d, list)
    print(present_diff(d))


_usage = """\
Compute the difference between two Jupyter notebooks.

This is nbdiff from nbdime version {}.

Example usage:

  jupyter nbdiff before.ipynb after.ipynb patch.json
""".format(__version__)


def main_diff(afn, bfn, dfn):
    for fn in (afn, bfn):
        if not os.path.exists(fn):
            print("Missing file {}".format(fn))
            return 1

    a = nbformat.read(afn, as_version=4)
    b = nbformat.read(bfn, as_version=4)

    d = diff_notebooks(a, b)

    verbose = True
    if verbose:
        pretty_print_notebook_diff(d)

    with open(dfn, "w") as df:
        json.dump(d, df)
        # Verbose version:
        #json.dump(d, df, indent=4, separators=(",", ": "))
    return 0


def main():
    args = sys.argv[1:]
    if len(args) != 3:
        r = 1
    else:
        r = main_diff(*args)
    if r:
        print(_usage)
    sys.exit(r)
