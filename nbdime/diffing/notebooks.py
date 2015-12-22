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

from ..dformat import PATCH, SEQINSERT, SEQDELETE
#, INSERT, DELETE, REPLACE,
from ..dformat import decompress_diff

from .comparing import strings_are_similar
from .sequences import diff_sequence
from .generic import diff, diff_lists
from .snakes import compute_snakes_multilevel

__all__ = ["diff_notebooks"]


def diff_single_cells(a, b):
    # TODO: Something smarter?
    # TODO: Use google-diff-patch-match library to diff the sources?
    # TODO: Handle output diffing with plugins? I.e. image diff, svg diff, json diff, etc.
    from nbdime import diff
    return diff(a, b)


def compare_cell_source_approximate(x, y):
    "Compare source of cells x,y with approximate heuristics."
    if x["cell_type"] != y["cell_type"]:
        return False
    # TODO: Use google-diff-patch-match library
    # TODO: Initially try difflib ratio
    return strings_are_similar(x["source"], y["source"])


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
    if x["cell_type"] == "code" and x["outputs"] != y["outputs"]:
        return False
    return True


def diff_cells(a, b):
    "Diff cell lists a and b."

    # Predicates to compare cells in order of low-to-high precedence
    predicates = [compare_cell_source_approximate,
                  compare_cell_source_exact,
                  compare_cell_source_and_outputs]

    # Invoke multilevel snake computation algorithm
    level = len(predicates) - 1
    rect = (0, 0, len(a), len(b))
    snakes = compute_snakes_multilevel(a, b, rect, predicates, level)

    # Compute diff from snakes
    di = []
    i0, j0, i1, j1 = 0, 0, len(a), len(b)
    for i, j, n in snakes + [(i1, j1, 0)]:
        if i > i0:
            di.append([SEQDELETE, i0, i-i0])
        if j > j0:
            di.append([SEQINSERT, i0, b[j0:j]])
        for k in range(n):
            cd = diff_single_cells(a[i + k], b[j + k])
            if cd:
                di.append([PATCH, i+k, cd])
        # Update corner offsets for next rectangle
        i0, j0 = i+n, j+n
    return di


def old_diff_cells(cells_a, cells_b):
    "Compute the diff of two sequences of cells."
    shallow_diff = diff_sequence(cells_a, cells_b, compare_cells)
    return diff_lists(cells_a, cells_b, compare=operator.__eq__, shallow_diff=shallow_diff)


def diff_notebooks(nba, nbb):
    """Compute the diff of two notebooks.

    Simliar to diff(), but handles cells in specialized ways.
    """

    # Shallow copy dicts and pop "cells"
    nba = nba.copy()
    nbb = nbb.copy()
    acells = nba.pop("cells")
    bcells = nbb.pop("cells")

    # Diff the rest of the notebook using generic tools
    nbdiff = diff(nba, nbb)

    # Then apply a specialized approach to diffing cells
    cdiff = diff_cells(acells, bcells)
    if cdiff:
        nbdiff.append([PATCH, "cells", cdiff])

    return nbdiff
