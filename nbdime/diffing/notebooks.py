# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.
"""

import difflib
import operator
from six import string_types

from ..diff_format import source_as_string

from .sequences import diff_sequence
from .generic import diff, diff_lists, diff_dicts
from .snakes import diff_sequence_multilevel

__all__ = ["diff_notebooks"]


def compare_cell_source_approximate(x, y):
    "Compare source of cells x,y with approximate heuristics."
    # Cell types must match
    if x.cell_type != y["cell_type"]:
        return False

    # Convert from list to single string
    xs = source_as_string(x["source"])
    ys = source_as_string(y["source"])

    # Cutoff on equality (Python has fast hash functions for strings)
    if xs == ys:
        return True

    # TODO: Investigate performance and quality of this difflib ratio approach,
    # possibly one of the weakest links of the notebook diffing algorithm.
    # Alternatives to try are the libraries diff-patch-match and Levenschtein
    threshold = 0.7  # TODO: Add configuration framework and tune with real world examples?

    # Informal benchmark normalized to operator ==:
    #    1.0  operator ==
    #  438.2  real_quick_ratio
    #  796.5  quick_ratio
    # 3088.2  ratio
    # The == cutoff will hit most of the time for long runs of
    # equal items, at least in the Myers diff algorithm.
    # Most other comparisons will likely not be very similar,
    # and the (real_)quick_ratio cutoffs will speed up those.
    # So the heavy ratio function is only used for close calls.
    #s = difflib.SequenceMatcher(lambda c: c in (" ", "\t"), x, y, autojunk=False)
    s = difflib.SequenceMatcher(None, xs, ys, autojunk=False)
    if s.real_quick_ratio() < threshold:
        return False
    if s.quick_ratio() < threshold:
        return False
    return s.ratio() > threshold


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

    if ot == "stream":
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


def diff_single_outputs(a, b, compare="ignored", path="/cells/*/output/*"):
    "Diff a pair of output cells."
    assert path == "/cells/*/outputs/*"
    # TODO: Handle output diffing with plugins? I.e. image diff, svg diff, json diff, etc.
    # FIXME: Use linebased diff of some types of outputs:
    # if a.output_type in ("execute_result", "display_data"):
    #    a.data.key if key.startswith('text/') or key in _non_text_split_mimes = {
    #        'application/javascript','image/svg+xml'}
    #    a.text
    return diff(a, b)

# TODO: This is now equal to diff_cells, after some refactoring steps towards generalization
def diff_outputs(a, b, compare="ignored", path="/cells/*/outputs"):
    "Diff a pair of lists of outputs from within a single cell."
    assert path == "/cells/*/outputs"
    predicates = notebook_predicates[path]
    return diff_sequence_multilevel(a, b, predicates, path=path, differs=notebook_differs)


def diff_source(a, b, compare="ignored", path="/cells/*/source"):
    "Diff a pair of sources."
    assert path == "/cells/*/source"
    # FIXME: Make sure we use linebased diff of sources
    # TODO: Use google-diff-patch-match library to diff the sources?
    return diff(a, b)


def diff_single_cells(a, b, path="/cells/*"):
    assert path == "/cells/*"
    return diff_dicts(a, b, path=path, differs=notebook_differs)

def diff_cells(a, b, compare="ignored", path="/cells"):
    "Diff cell lists a and b. Argument compare is ignored."
    assert path == "/cells"
    # Predicates to compare cells in order of low-to-high precedence
    predicates = notebook_predicates[path]
    return diff_sequence_multilevel(a, b, predicates, path=path, differs=notebook_differs)


def diff_notebooks(a, b, path=""):
    """Compute the diff of two notebooks."""
    assert path == ""
    return diff_dicts(a, b, path=path, subdiffs={"cells": diff_cells})


# Sequence diffs should be applied with multilevel
# algorithm for paths with more than one predicate,
# and using operator.__eq__ if no match in there.
notebook_predicates = {
    "/cells": [
        compare_cell_source_approximate,
        compare_cell_source_exact,
        compare_cell_source_and_outputs,
        ],
    "/cells/*/outputs": [
        compare_output_data_keys,
        compare_output_data,
        ]
    }

# Recursive diffing of substructures should pick a rule from here, with diff as fallback
notebook_differs = {
    "": diff_notebooks,
    "/cells": diff_cells,
    "/cells/*": diff_single_cells,
    "/cells/*/source": diff_source,
    "/cells/*/outputs": diff_outputs,
    "/cells/*/outputs/*": diff_single_outputs,
    }
