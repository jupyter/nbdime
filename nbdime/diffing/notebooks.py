# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.
"""

__all__ = ["diff_notebooks"]

import operator

from ..dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE
from ..dformat import decompress_diff

from .comparing import strings_are_similar
from .sequences import diff_sequence
from .generic import diff, diff_lists


def compare_cells(a, b):
    # If we get something different from a cell, fall back to ==.
    # TODO: Should avoid this situation and make sure compare_cells is only applied
    # to cells, e.g. by handling path-specific comparison predicates in diff()
    if not (isinstance(a, dict) and "source" in a and isinstance(b, dict) and "source" in b):
        return a == b

    # Quick cutoff on cell type
    if a["cell_type"] != b["cell_type"]:
        return False

    # Make source code the decisive source of cell similarity,
    # ignoring execution_count, metadata, and outputs
    sa = a["source"]
    sb = b["source"]
    return strings_are_similar(sa, sb)


def diff_cells(cells_a, cells_b):
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

    # Diff the rest
    nbdiff = diff(nba, nbb)

    # Then add specialized cells diff
    cdiff = diff_cells(acells, bcells)
    if cdiff:
        nbdiff.append([PATCH, "cells", cdiff])

    return nbdiff
