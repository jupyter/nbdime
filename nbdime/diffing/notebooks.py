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
import copy
from collections import defaultdict

from ..diff_format import source_as_string, MappingDiffBuilder

from .generic import (diff, diff_sequence_multilevel,
                      compare_strings_approximate)

__all__ = ["diff_notebooks"]


def compare_cell_source_approximate(x, y):
    "Compare source of cells x,y with approximate heuristics."
    # Cell types must match
    if x.cell_type != y["cell_type"]:
        return False

    # Convert from list to single string
    xs = source_as_string(x["source"])
    ys = source_as_string(y["source"])

    return compare_strings_approximate(xs, ys)


def compare_cell_source_exact(x, y):
    "Compare source of cells x,y exactly."
    if x["cell_type"] != y["cell_type"]:
        return False
    if x["source"] != y["source"]:
        return False
    return True


def compare_cell_source_and_outputs(x, y):
    "Compare source and outputs of cells x,y exactly."
    if x["cell_type"] != y["cell_type"]:
        return False
    if x["source"] != y["source"]:
        return False
    if x["cell_type"] == "code":
        if x["outputs"] != y["outputs"]:
            return False
    # NB! Ignoring metadata and execution count
    return True


def compare_output_type(x, y):
    "Compare only type of output cells x,y."
    if x["output_type"] != y["output_type"]:
        return False
    # NB! Ignoring metadata and execution count
    return True


def compare_output_data_keys(x, y):
    "Compare type and data of output cells x,y exactly."
    ot = x["output_type"]
    if ot != y["output_type"]:
        return False

    if ot == "stream" or ot == "error":
        pass
    else:  # if ot == "display_data" or ot == "execute_result":
        if set(x["data"].keys()) != set(y["data"].keys()):
            return False

    # NB! Ignoring metadata and execution count
    return True


def compare_output_data(x, y):
    "Compare type and data of output cells x,y exactly."
    ot = x["output_type"]
    if ot != y["output_type"]:
        return False

    if ot == "stream":
        if x["name"] != y["name"]:
            return False
        if x["text"] != y["text"]:
            return False
    elif ot == "error":
        if x["evalue"] != y["evalue"]:
            return False
        if x["ename"] != y["ename"]:
            return False
        if x["traceback"] != y["traceback"]:
            return False
    else:  # if ot == "display_data" or ot == "execute_result":
        if set(x["data"].keys()) != set(y["data"].keys()):
            return False
        if x["metadata"] != y["metadata"]:
            return False
        # TODO: approximate mime-specific output data comparison?
        if x["data"] != y["data"]:
            return False

    # NB! Ignoring metadata and execution count
    return True


def diff_single_outputs(a, b, path="/cells/*/output/*",
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


def diff_attachments(a, b, path="/cells/*/attachments",
                     predicates=None, differs=None):
    """Diff a pair of attachment collections"""
    assert path == "/cells/*/attachments"

    # Two events can happen:
    #  1: An attachment is added/removed/patched
    #  2: An attachment is renamed (key change)
    # Currently, #2 is handled as two ops (an add and a remove)

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

        if key.lower().startswith(_split_mimes):
            dd = diff_mime_bundle(avalue, bvalue)
            if dd:
                di.patch(key, dd)
        elif avalue != bvalue:
            di.replace(key, bvalue)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])
    return di.validated()



_split_mimes = ('text/', 'image/svg+xml', 'application/javascript', 'application/json')


def diff_mime_bundle(a, b, path=None,
                     predicates=None, differs=None):
    assert isinstance(a, dict) and isinstance(b, dict)
    di = MappingDiffBuilder()

    akeys = set(a.keys())
    bkeys = set(b.keys())
    # Sorting keys in loops to get a deterministic diff result
    for key in sorted(akeys - bkeys):
        di.remove(key)

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]

        # TODO: Handle output diffing with plugins?
        # I.e. image diff, svg diff, json diff, etc.
        if key.lower().startswith(_split_mimes):
            dd = diff(avalue, bvalue)
            if dd:
                di.patch(key, dd)
        elif avalue != bvalue:
            di.replace(key, bvalue)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])
    return di.validated()


# Sequence diffs should be applied with multilevel
# algorithm for paths with more than one predicate,
# and using operator.__eq__ if no match in there.
notebook_predicates = defaultdict(lambda: [operator.__eq__], {
    # Predicates to compare cells in order of low-to-high precedence
    "/cells": [
        compare_cell_source_approximate,
        compare_cell_source_exact,
        compare_cell_source_and_outputs,
        ],
    # Predicates to compare output cells (within one cell) in order of low-to-high precedence
    "/cells/*/outputs": [
        compare_output_data_keys,
        compare_output_data,
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
