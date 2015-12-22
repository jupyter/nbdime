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
from .log import error
from .diffing.notebooks import diff_notebooks
from .dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE


from .dformat import to_dict_diff
import pprint


action_names = {
    DELETE: "delete",
    INSERT: "insert",
    REPLACE: "replace",
    SEQDELETE: "delete",
    SEQINSERT: "insert",
    PATCH: "patch",
    }


def present_value(prefix, arg):
    # TODO: improve pretty-print of arbitrary values?
    lines = pprint.pformat(arg).splitlines()
    return [prefix + line for line in lines]


def present_dict_diff(a, b, d):
    "Pretty-print a nbdime diff."

    d = to_dict_diff(d)
    keys = sorted(d)

    pp = []
    for key in keys:
        e = d[key]
        action = e[0]
        arg = e[1] if len(e) > 1 else None

        actname = action_names[action]

        if action == DELETE:
            pp.append("-  a[{}]".format(key))
            pp += present_value("- ", a[key])

        elif action == INSERT:
            pp.append(" + b[{}]".format(key))
            pp += present_value("+ ", arg)

        elif action == REPLACE:
            pp.append("-+ a[{}] <- b[{}]".format(key, key))
            pp += present_value("- ", a[key])
            pp += present_value(" +", arg)

        elif action == PATCH:
            pp.append("!! a[{}], b[{}]".format(key, key))
            pp += present_diff(a[key], b[key], arg)

        else:
            error("Can't print {}: {}".format(key, actname))

    return pp


def present_list_diff(a, b, d):
    "Pretty-print a nbdime diff."
    pp = []
    for e in d:
        action = e[0]
        index = e[1]
        arg = e[2] if len(e) > 2 else None

        actname = action_names[action]

        if action == DELETE:
            pp.append("-  a[{}]".format(index))
            pp += present_value("- ", a[index])

        elif action == INSERT:
            pp.append(" + b[{}]".format(index))
            pp += present_value("+ ", arg)

        elif action == SEQDELETE:
            pp.append("-  a[{}:{}]".format(index, index+arg))
            pp += present_value("- ", a[index:index+arg])

        elif action == SEQINSERT:
            pp.append(" + a[{}:{}]".format(index, index))
            pp += present_value("+ ", arg)

        elif action == PATCH:
            pp.append("!! a[{}], b[{}]".format(index))
            pp += present_diff(a[index], b[index], arg)

        else:
            error("Can't print {}: {}".format(index, actname))

    return pp


def present_diff(a, b, d, indent=True):
    indsep = " "*4
    ind = indsep*indent
    ind2 = indsep*(indent+1)

    if isinstance(a, dict) and isinstance(b, dict):
        pp = present_dict_diff(a, b, d)
    elif isinstance(a, list) and isinstance(b, list):
        pp = present_list_diff(a, b, d)
    elif isinstance(a, string_types) and isinstance(b, string_types):
        pp = present_string_diff(a, b, d)
    else:
        error("Invalid type for diff presentation.")

    # Optionally indent
    indsep = " "*4
    return [indsep + line for line in pp] if indent else pp


header = """\
nbdiff a/{afn} b/{bfn}
--- a/{afn}
+++ b/{bfn}
"""


def pretty_print_notebook_diff(afn, bfn, a, b, d):

    #d = to_dict_diff(d)
    #p = []
    #for key in ("metadata", "cells"):
    #    s = d.get(key)
    #    if s is not None:
    #        p += ['"{key}" differs:'.format(key=key)]
    #        p += present_diff(a[key], b[key], s)

    p = present_diff(a, b, d)
    if p:
        p = [header.format(afn=afn, bfn=bfn)] + p
    print("\n".join(p))

    #missing = set(d.keys()) - set(("metadata", "cells"))
    #if missing:
    #    print("FIXME: Missing in presentation:")
    #    print(missing)


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
        pretty_print_notebook_diff(afn, bfn, a, b, d)

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
