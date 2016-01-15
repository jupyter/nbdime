# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from six import string_types
import pprint

from .diffing.notebooks import diff_notebooks
from .dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE
from .dformat import to_dict_diff, NBDiffFormatError


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

        nextpath = "/".join((path, key))

        if action == DELETE:
            pp.append("delete from {}:".format(nextpath))
            pp += present_value("- ", a[key])

        elif action == INSERT:
            arg = e[1]
            pp.append("insert at {}:".format(nextpath))
            pp += present_value("+ ", arg)

        elif action == REPLACE:
            arg = e[1]
            pp.append("replace at {}:".format(nextpath))
            pp += present_value("- ", a[key])
            pp += present_value(" +", arg)

        elif action == PATCH:
            arg = e[1]
            pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[key], arg, nextpath)

        else:
            raise NBDiffFormatError("Unknown dict diff action {}".format(action))

    return pp


def present_list_diff(a, d, path):
    "Pretty-print a nbdime diff."
    pp = []
    for e in d:
        action = e[0]
        index = e[1]

        nextpath = "/".join((path, str(index)))

        if action == SEQINSERT:
            arg = e[2]
            pp.append("insert before {}:".format(nextpath))
            pp += present_value("+ ", arg)

        elif action == SEQDELETE:
            arg = e[2]
            if arg > 1:
                r = "{}-{}".format(index, index+arg-1)
            else:
                r = str(index)
            pp.append("delete {}/{}:".format(path, r))
            pp += present_value("- ", a[index:index+arg])

        elif action == PATCH:
            arg = e[2]
            pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[index], arg, nextpath)

        else:
            raise NBDiffFormatError("Unknown list diff action {}".format(action))

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
            raise NBDiffFormatError("Unknown string diff action {}".format(action))

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
        raise NBDiffFormatError("Invalid type {} for diff presentation.".format(type(a)))

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
