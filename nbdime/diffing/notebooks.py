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

from ..diff_format import source_as_string, MappingDiffBuilder, DiffOp

from .generic import (diff, diff_sequence_multilevel,
                      compare_strings_approximate)

__all__ = ["diff_notebooks"]


"""
compare_text_approximate
compare_text_strict
compare_mimedata_approximate
compare_mimedata_strict
compare_mimebundle_approximate
compare_mimebundle_strict
compare_source_approximate
compare_source_strict
compare_output_approximate
compare_output_strict
compare_cell_approximate
compare_cell_moderate
compare_cell_strict
"""


def compare_mimebundle_approximate(x, y):
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False

    # This only checks that the same mime types are present
    if set(x.keys()) != set(y.keys()):
        return False

    # TODO: Could do some size checking?
    # TODO: Compare contents of mime bundles approximately?

    return True


re_repr = re.compile(r"^<[a-zA-Z0-9._]+ at 0x[a-zA-Z0-9]+>$")


def compare_mimebundle_strict(x, y):
    # Get the simple and cheap stuff out of the way
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False

    # This only checks that the same mime types are present
    if set(x.keys()) != set(y.keys()):
        return False

    # FIXME: Allow some diff, e.g. on repr style text in text/plain
    dd = diff_mime_bundle(x, y)

    for e in dd:
        # Fail comparison for adds and removes
        if e.op != DiffOp.PATCH:
            return False

        # Treat some types of difference specifically
        if e.key == "text/plain":
            if re_repr.match(x[e.key]) and re_repr.match(y[e.key]):
                continue

    # Strict comparison:
    #if x != y:
    #    return False

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
        if len(xt) != len(yt):
            return False
        if not all(compare_strings_approximate(xt[i], yt[i]) for i in range(len(xt))):
            return False

        handled.update(("ename", "evalue", "traceback"))

    elif ot == "display_data" or ot == "execute_result":
        if not compare_mimebundle_approximate(x.get("data"), y.get("data")):
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
    if x.get("traceback") != y.get("traceback"):
        return False

    return compare_mimebundle_strict(x.get("data"), y.get("data"))


def compare_cell_approximate(x, y):
    "Compare source of cells x,y with approximate heuristics."
    # Cell types must match
    if x.cell_type != y["cell_type"]:
        return False

    # Convert from list to single string
    xs = source_as_string(x["source"])
    ys = source_as_string(y["source"])

    return compare_strings_approximate(xs, ys)


def compare_cell_moderate(x, y):
    "Compare source of cells x,y exactly."
    if x["cell_type"] != y["cell_type"]:
        return False
    if x["source"] != y["source"]:
        return False
    return True


def compare_cell_strict(x, y):
    "Compare source and outputs of cells x,y exactly."
    if x["cell_type"] != y["cell_type"]:
        return False
    if x["source"] != y["source"]:
        return False
    if x["cell_type"] == "code":
        if x["outputs"] != y["outputs"]:
            return False
    # NB! Ignoring metadata and execution count of cell
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


_text_mimes = ('text/', 'image/svg+xml', 'application/javascript', 'application/json')


def add_mime_diff(key, avalue, bvalue, diffbuilder):
    # TODO: Handle output diffing with plugins?
    # I.e. image diff, svg diff, json diff, etc.
    if key.lower().startswith(_text_mimes):
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
