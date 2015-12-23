"""Utilities for diffing notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from six import string_types
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


def present_dict_diff(a, d, path):
    "Pretty-print a nbdime diff."

    d = to_dict_diff(d)
    keys = sorted(d)

    pp = []
    for key in keys:
        e = d[key]
        action = e[0]
        arg = e[1] if len(e) > 1 else None

        actname = action_names[action]
        nextpath = "/".join((path, key))

        if action == DELETE:
            pp.append("delete from {}:".format(nextpath))
            pp += present_value("- ", a[key])

        elif action == INSERT:
            pp.append("insert at {}:".format(nextpath))
            pp += present_value("+ ", arg)

        elif action == REPLACE:
            pp.append("replace at {}:".format(nextpath))
            pp += present_value("- ", a[key])
            pp += present_value(" +", arg)

        elif action == PATCH:
            pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[key], arg, nextpath)

        else:
            error("Can't print {}: {}".format(key, actname))

    return pp


def present_list_diff(a, d, path):
    "Pretty-print a nbdime diff."
    pp = []
    for e in d:
        action = e[0]
        index = e[1]
        arg = e[2] if len(e) > 2 else None

        actname = action_names[action]
        nextpath = "/".join((path, str(index)))

        if action == SEQINSERT:
            pp.append("insert before {}:".format(nextpath))
            pp += present_value("+ ", arg)

        elif action == SEQDELETE:
            if arg > 1:
                r = "{}-{}".format(index, index+arg-1)
            else:
                r = str(index)
            pp.append("delete {}/{}:".format(path, r))
            pp += present_value("- ", a[index:index+arg])

        elif action == PATCH:
            pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[index], arg, nextpath)

        else:
            error("Can't print {}: {}".format(index, actname))

    return pp


def present_string_diff(a, d, path):
    "Pretty-print a nbdime diff."

    consumed = 0
    lines = []
    continuation = False
    continuation_indent = 0
    continuation_indent2 = 0
    for e in d:
        action = e[0]
        index = e[1]
        arg = e[2]

        # Consume untouched characters
        if index > consumed:
            dlines = a[consumed:index].split("\n")
            for dline in dlines:
                prefix = ".." if continuation else "  "
                lines.append(prefix + " "*continuation_indent2 + dline)
                continuation = False
                continuation_indent2 = 0
            continuation_indent = len(lines[-1]) - 2
            continuation_indent2 = continuation_indent
            consumed = index

        if action == SEQINSERT:
            dlines = arg.split("\n")
            lines.append("+ " + " "*continuation_indent + dlines[0])
            for dline in dlines[1:]:
                lines.append("+ " + dline)
            continuation = True
            continuation_indent2 = max(continuation_indent2, len(lines[-1]) - 2)

        elif action == SEQDELETE:
            dlines = a[index:index+arg].split("\n")
            lines.append("- " + " "*continuation_indent + dlines[0])
            for dline in dlines[1:]:
                lines.append("- " + dline)
            consumed = index + arg
            continuation = True
            continuation_indent2 = max(continuation_indent2, len(lines[-1]) - 2)

        else:
            error("Can't print {}: {}".format(index, actname))

    # Consume untouched characters at end
    index = len(a)  # copy-paste from top of loop...
    if index > consumed:
        dlines = a[consumed:index].split("\n")
        for dline in dlines:
            prefix = ".." if continuation else "  "
            lines.append(prefix + " "*continuation_indent2 + dline)
            continuation = False
            continuation_indent2 = 0
        continuation_indent = len(lines[-1]) - 2
        continuation_indent2 = continuation_indent
        consumed = index

    return lines


def present_diff(a, d, path, indent=True):
    "Pretty-print a nbdime diff."
    if isinstance(a, dict):
        pp = present_dict_diff(a, d, path)
    elif isinstance(a, list):
        pp = present_list_diff(a, d, path)
    elif isinstance(a, string_types):
        pp = present_string_diff(a, d, path)
    else:
        error("Invalid type for diff presentation.")

    # Optionally indent
    indsep = " "*2
    return [indsep + line for line in pp] if indent else pp


header = """\
nbdiff {afn} {bfn}
--- a: {afn}
+++ b: {bfn}
"""


def pretty_print_notebook_diff(afn, bfn, a, d):
    p = present_diff(a, d, path="a", indent=False)
    if p:
        p = [header.format(afn=afn, bfn=bfn)] + p
    print("\n".join(p))


_usage = """\
Compute the difference between two Jupyter notebooks.

This is nbdiff from nbdime version {}.

Example usage:

  jupyter nbdiff before.ipynb after.ipynb patch.json
""".format(__version__)


def main_diff(afn, bfn, dfn=None):
    for fn in (afn, bfn):
        if not os.path.exists(fn):
            print("Missing file {}".format(fn))
            return 1

    a = nbformat.read(afn, as_version=4)
    b = nbformat.read(bfn, as_version=4)

    d = diff_notebooks(a, b)

    verbose = True
    if verbose:
        pretty_print_notebook_diff(afn, bfn, a, d)

    if dfn is not None:
        with open(dfn, "w") as df:
            json.dump(d, df)
            # Verbose version:
            #json.dump(d, df, indent=4, separators=(",", ": "))
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
