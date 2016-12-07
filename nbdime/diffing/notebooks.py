# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.
"""

import operator
import re
import copy
from collections import defaultdict
from six import string_types
from six.moves import zip

from ..diff_format import source_as_string, MappingDiffBuilder, DiffOp

from .generic import (diff, diff_sequence_multilevel,
                      compare_strings_approximate)

__all__ = ["diff_notebooks"]

# A regexp matching base64 encoded data
_base64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', re.MULTILINE | re.UNICODE)

# A regexp matching common python repr-style output like
# <module.type at 0xmemoryaddress>
re_repr = re.compile(r"<[a-zA-Z0-9._]+ at 0x[a-zA-Z0-9]+>")


# List of mimes we can diff recursively
_text_mimes = (
    'text/',
    'image/svg+xml',
    'application/javascript',
    'application/json',
    )
_split_mimes = (
    'text/',
    'image/svg+xml',
    'application/javascript',
    'application/json',
    )


# TODO: Maybe cleaner to make the split between strict/approximate
#       an argument instead of separate functions.


def compare_text_approximate(x, y):
    if isinstance(x, list):
        x = "".join(x)
    if isinstance(y, list):
        y = "".join(y)
    return compare_strings_approximate(x, y)


def compare_text_strict(x, y):
    # TODO: Doesn't have to be 100% equal here?
    return x == y


def compare_base64_approximate(x, y):
    if len(x) != len(y):
        return False
    # TODO: Handle base64 data another way?
    return compare_strings_approximate(x, y)


def compare_base64_strict(x, y):
    if len(x) != len(y):
        return False
    # TODO: Handle base64 data another way?
    return x == y


def _compare_mimedata(mimetype, x, y, comp_text, comp_base64):
    mimetype = mimetype.lower()

    # TODO: Test this. Match repr-style oneliners with random pointer
    if mimetype == "text/plain":
        if "\n" not in x and "\n" not in y:
            if re_repr.match(x) and re_repr.match(y):
                return True

    if mimetype.startswith("text/"):
        return comp_text(x, y)

    # TODO: Compare binary images?
    #if mimetype.startswith("image/"):

    if isinstance(x, string_types) and isinstance(y, string_types):
        # Most likely base64 encoded data
        if _base64.match(x):
            return comp_base64(x, y)
        else:
            return comp_text(x, y)

    # Fallback to exactly equal
    return x == y


def compare_mimedata_approximate(mimetype, x, y):
    return _compare_mimedata(mimetype, x, y,
        compare_text_approximate, compare_base64_approximate)


def compare_mimedata_strict(mimetype, x, y):
    return _compare_mimedata(mimetype, x, y,
        compare_text_strict, compare_base64_strict)


def compare_mimebundle_approximate(x, y):
    # Get the simple and cheap stuff out of the way
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False

    # This only checks that the same mime types are present
    if set(x.keys()) != set(y.keys()):
        return False

    dd = diff_mime_bundle(x, y)
    for e in dd:
        # Fail comparison for adds and removes
        if e.op != DiffOp.PATCH:
            return False
        # Delegate to mimetype specific comparison
        if not compare_mimedata_approximate(e.key, x[e.key], y[e.key]):
            return False

    # Didn't fail up to here it must be equal
    return True


def compare_mimebundle_strict(x, y):
    # Get the simple and cheap stuff out of the way
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False

    # This only checks that the same mime types are present
    if set(x.keys()) != set(y.keys()):
        return False

    dd = diff_mime_bundle(x, y)
    for e in dd:
        # Fail comparison for adds and removes
        if e.op != DiffOp.PATCH:
            return False
        # Delegate to mimetype specific comparison
        if not compare_mimedata_strict(e.key, x[e.key], y[e.key]):
            return False

    # Didn't fail up to here it must be equal
    return True


def compare_tracebacks(xt, yt):
    if len(xt) != len(yt):
        return False
    for x, y in zip(xt, yt):
        if not compare_strings_approximate(x, y):
            return False
    return True


def compare_output_approximate(x, y):
    "Compare type and data of output cells x,y approximately."
    # NB! This is used as a basis by the exact compare_output.

    # Fast cutuff
    ot = x["output_type"]
    if ot != y["output_type"]:
        return False

    # Sanity cutoff
    xkeys = set(x)
    ykeys = set(y)
    if xkeys != ykeys:
        return False

    # Deliberately skipping metadata and execution count here
    handled = set(("output_type", "metadata", "execution_count"))

    if ot == "stream":
        if x["name"] != y["name"]:
            return False
        if not compare_strings_approximate(x["text"], y["text"]):
            return False
        handled.update(("name", "text"))

    elif ot == "error":
        if x["ename"] != y["ename"]:
            return False
        if x["evalue"] != y["evalue"]:
            return False

        # Compare tracebacks
        xt = x["traceback"]
        yt = y["traceback"]
        if not compare_tracebacks(xt, yt):
            return False

        handled.update(("ename", "evalue", "traceback"))

    elif ot == "display_data" or ot == "execute_result":
        xd = x["data"]
        yd = y["data"]
        if not compare_mimebundle_approximate(xd, yd):
            return False
        handled.update(("data",))

    else:
        # Unknown type
        pass

    # Play safe on unknown keys
    for k in xkeys - handled:
        if x[k] != y[k]:
            return False

    # NB! Ignoring metadata and execution count
    return True


def compare_output_strict(x, y):
    "Compare type and data of output cells x,y to higher accuracy."
    # Fall back on approximate checks first
    if not compare_output_approximate(x, y):
        return False

    # Add strict checks on fields ignored in approximate version
    if x.get("metadata") != y.get("metadata"):
        return False
    #if x.get("traceback") != y.get("traceback"):
    #    return False

    return compare_mimebundle_strict(x.get("data"), y.get("data"))


def compare_cell_approximate(x, y):
    "Compare cells x,y with approximate heuristics."
    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
        return False

    # Compare sources
    if not compare_text_approximate(x["source"], y["source"]):
        return False

    # NB! Ignoring metadata, execution_count, outputs
    return True


def compare_cell_moderate(x, y):
    "Compare cells x,y with moderate accuracy heuristics."
    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
        return False

    # Compare sources
    if not compare_text_approximate(x["source"], y["source"]):
        return False

    # Compare outputs for code cells
    if x["cell_type"] == "code":
        xop = x["outputs"] or ()
        yop = y["outputs"] or ()
        if len(xop) != len(yop):
            return False
        for xo, yo in zip(xop, yop):
            if not compare_output_approximate(xo, yo):
                return False

    # NB! Ignoring metadata and execution_count
    return True


def compare_cell_strict(x, y):
    "Compare cells x,y with higher accuracy heuristics."
    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
        return False

    # Compare sources
    if not compare_text_strict(x["source"], y["source"]):
        return False

    # Compare outputs for code cells
    if x["cell_type"] == "code":
        xop = x["outputs"] or ()
        yop = y["outputs"] or ()
        if len(xop) != len(yop):
            return False
        for xo, yo in zip(xop, yop):
            if not compare_output_strict(xo, yo):
                return False

    # NB! Ignoring metadata and execution count
    return True


def diff_single_outputs(a, b, path="/cells/*/outputs/*",
                        predicates=None, differs=None):
    "DiffOp a pair of output cells."
    assert path == "/cells/*/outputs/*"
    assert a.output_type == b.output_type

    if a.output_type in ("execute_result", "display_data"):
        di = MappingDiffBuilder()

        a_conj = copy.deepcopy(a)
        del a_conj['data']
        b_conj = copy.deepcopy(b)
        del b_conj['data']
        dd_conj = diff(a_conj, b_conj)
        if dd_conj:
            for e in dd_conj:
                di.append(e)

        dd = diff_mime_bundle(a.data, b.data, path=path+"/data")
        if dd:
            di.patch("data", dd)

        return di.validated()
    else:
        return diff(a, b)


def add_mime_diff(key, avalue, bvalue, diffbuilder):
    # TODO: Handle output diffing with plugins?
    # I.e. image diff, svg diff, json diff, etc.

    mimetype = key.lower()
    if any(mimetype.startswith(tm) for tm in _split_mimes):
        dd = diff(avalue, bvalue)
        if dd:
            diffbuilder.patch(key, dd)
    elif avalue != bvalue:
        diffbuilder.replace(key, bvalue)


def diff_attachments(a, b, path="/cells/*/attachments",
                     predicates=None, differs=None):
    """Diff a pair of attachment collections"""
    assert path == "/cells/*/attachments"

    # Two events can happen:
    #  1: An attachment is added/removed/patched
    #  2: An attachment is renamed (key change)
    # Currently, #2 is handled as two ops (an add and a remove)

    # keys here are 'filenames' of the attachments
    assert isinstance(a, dict) and isinstance(b, dict)
    akeys = set(a.keys())
    bkeys = set(b.keys())

    di = MappingDiffBuilder()

    # Sorting keys in loops to get a deterministic diff result
    for key in sorted(akeys - bkeys):
        di.remove(key)

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]

        dd = diff_mime_bundle(avalue, bvalue)
        if dd:
            di.patch(key, dd)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])
    return di.validated()


def diff_mime_bundle(a, b, path=None,
                     predicates=None, differs=None):
    # keys here are mime/types
    assert isinstance(a, dict) and isinstance(b, dict)
    akeys = set(a.keys())
    bkeys = set(b.keys())

    di = MappingDiffBuilder()

    # Sorting keys in loops to get a deterministic diff result
    for key in sorted(akeys - bkeys):
        di.remove(key)

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]
        add_mime_diff(key, avalue, bvalue, di)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])
    return di.validated()


# Sequence diffs should be applied with multilevel
# algorithm for paths with more than one predicate,
# and using operator.__eq__ if no match in there.
notebook_predicates = defaultdict(lambda: [operator.__eq__], {
    # Predicates to compare cells in order of low-to-high precedence
    "/cells": [
        compare_cell_approximate,
        compare_cell_moderate,
        compare_cell_strict,
        ],
    # Predicates to compare output cells (within one cell) in order of low-to-high precedence
    "/cells/*/outputs": [
        compare_output_approximate,
        compare_output_strict,
        ]
    })


# Recursive diffing of substructures should pick a rule from here, with diff as fallback
notebook_differs = defaultdict(lambda: diff, {
    "/cells": diff_sequence_multilevel,
    "/cells/*": diff,
    "/cells/*/outputs": diff_sequence_multilevel,
    "/cells/*/outputs/*": diff_single_outputs,
    "/cells/*/attachments": diff_attachments,
    })


def diff_cells(a, b):
    "This is currently just used by some tests."
    path = "/cells"
    return notebook_differs[path](a, b, path=path, predicates=notebook_predicates, differs=notebook_differs)


def diff_notebooks(a, b):
    """Compute the diff of two notebooks using customized heuristics and diff rules."""
    return diff(a, b, path="", predicates=notebook_predicates, differs=notebook_differs)
