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

from ..dformat import source_as_string

from .sequences import diff_sequence
from .generic import diff, diff_lists, diff_dicts
from .snakes import diff_sequence_multilevel

__all__ = ["diff_notebooks"]


def compare_cell_source_approximate(x, y):
    "Compare source of cells x,y with approximate heuristics."
    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
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
        #d = diff(x["text"], y["text"])
        #return bool(d)  # FIXME
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


def diff_source(a, b, compare="ignored"):
    "Diff a pair of sources."
    # FIXME: Make sure we use linebased diff of sources
    # TODO: Use google-diff-patch-match library to diff the sources?
    return diff(a, b)


def diff_single_outputs(a, b, compare="ignored"):
    "Diff a pair of output cells."
    # TODO: Handle output diffing with plugins? I.e. image diff, svg diff, json diff, etc.
    return diff(a, b)


def diff_outputs(a, b, compare="ignored"):
    "Diff a pair of lists of outputs from within a single cell."
    predicates = [compare_output_data_keys,
                  compare_output_data]
    return diff_sequence_multilevel(a, b, predicates, diff_single_outputs)


def diff_single_cells(a, b):
    return diff_dicts(a, b, subdiffs={"source": diff_source, "outputs": diff_outputs})


def diff_cells(a, b, compare="ignored"):
    "Diff cell lists a and b. Argument compare is ignored."
    # Old alternative implementation:
    # shallow_diff = diff_sequence(a, b, compare_cell_source_and_outputs)
    # return diff_lists(a, b, compare=operator.__eq__, shallow_diff=shallow_diff)

    # Predicates to compare cells in order of low-to-high precedence
    predicates = [compare_cell_source_approximate,
                  compare_cell_source_exact,
                  compare_cell_source_and_outputs]
    return diff_sequence_multilevel(a, b, predicates, diff_single_cells)


def diff_notebooks(nba, nbb):
    """Compute the diff of two notebooks."""
    try:
        r = diff_dicts(nba, nbb, subdiffs={"cells": diff_cells})
    except Exception as e:
        import IPython
        IPython.embed()
        raise
    return r
