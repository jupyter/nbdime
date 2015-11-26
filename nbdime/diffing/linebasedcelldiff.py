# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""Experimental utilities for flattened linebased diff of cells.

These are not tested or functional, considering whether
to throw it away or develop the idea further.
"""

__all__ = ["diff_cells_linebased"]

import copy
import nbformat

from ..dformat import decompress_diff
from ..patching import patch

from .deep import deep_diff


def extract_source_lines(cells):
    lines = []
    cell_offsets = []
    origin_cell_numbers = []
    for i, cell in enumerate(cells):
        # Get source as a list of single-line strings without newlines
        source = cell["source"]
        if isinstance(source, basestring):
            source = source.splitlines()

        # Store the offset into the concatenated lines
        cell_offsets.append(len(lines))

        # Concatenate lines from this cell
        lines.extend(source)

        # Store which cell number each concatenated line originates from
        origin_cell_numbers.extend(i for j in range(len(source)))

        # Note: The local line number in the origin cell is
        #local_line = global_line - cell_offsets[origin_cell_numbers[global_line]]

    return lines, cell_offsets, origin_cell_numbers


def build_line_to_line_number_mapping(lines_a, lines_b, line_diff):
    aln = 0 # Line number into lines_a
    bln = 0 # Line number into lines_b
    a2b = [None]*len(lines_a) # a2b[i] = j  ===  line i from a is located at line j in b, missing in b if j=-1
    b2a = [None]*len(lines_b) # vice versa
    for s in line_diff:
        action = s[0]
        index = s[1]

        # Range aln:index not mentioned in diff,
        # corresponds to a range of equal lines
        n = index - aln
        for i in range(n):
            a2b[aln + i] = bln + i
            b2a[bln + i] = aln + i
        aln += n
        bln += n
        assert a2b[aln] is None
        assert b2a[bln] is None

        if action == "+":
            # Line s[2] inserted before lines_a[s[1]]
            assert s[1] == aln
            assert s[2] is lines_b[bln]
            b2a[bln] = -1
            bln += 1
        elif action == "-":
            # Line lines_a[s[1]] deleted
            assert s[1] == aln
            a2b[aln] = -1
            aln += 1
        elif action == ":":
            # Line lines_a[s[1]] replaced with s[2]
            assert s[1] == aln
            assert s[2] is lines_b[bln]
            a2b[aln] = bln
            b2a[bln] = aln
            aln += 1
            bln += 1
        elif action == "!":
            # Line lines_a[s[1]] patched with diff s[2] to produce lines_b[bln]
            # (I don't think this occurs at the time being)
            assert s[1] == aln
            assert patch(lines_a[aln], s[2]) == lines_b[bln]
            a2b[aln] = bln
            b2a[bln] = aln
            aln += 1
            bln += 1
    return a2b, b2a


def build_line_to_cell_number_mapping(a2b, b2a, origin_cell_numbers_a, origin_cell_numbers_b):
    a2bc = [-1 if j == -1 else origin_cell_numbers_b[j]
            for aln, j in enumerate(a2b)]
    b2ac = [-1 if j == -1 else origin_cell_numbers_a[j]
            for bln, j in enumerate(b2a)]
    return a2bc, b2ac


def build_cell_to_cell_numbers_mapping(a2bc, b2ac,
                                       cell_offsets_a, origin_cell_numbers_a,
                                       cell_offsets_b, origin_cell_numbers_b):
    # Note: The local line number in the origin cell is
    #local_line = global_line - cell_offsets[origin_cell_numbers[global_line]]

    nca = len(origin_cell_numbers_a)
    ncb = len(origin_cell_numbers_b)

    # Could optimize storage here with a crs-like array
    ac2bc = [[] for _ in range(nca)]
    bc2ac = [[] for _ in range(ncb)]

    for aln, bc in enumerate(a2bc):
        # line aln in ac moved to bc
        if bc != -1:
            ac2bc[origin_cell_numbers_a[aln]].append(bc)

    for bln, ac in enumerate(b2ac):
        # line bln in bc originates in ac
        if ac != -1:
            bc2ac[origin_cell_numbers_b[bln]].append(ac)

    # Build counts of how many different b-cells each a-cell maps to and vice versa
    ac2nbcs = [len(set(bcs)) for bcs in ac2bc]
    bc2nacs = [len(set(acs)) for acs in bc2ac]

    # Cell diff building pseudocode:
    d = []
    k = 0 # Next line diff entry
    #line_diff[k]
    for ac, nbcs in enumerate(ac2nbcs):
        # Delete cell ac if it doesn't map to any cell in b
        if nbcs == 0:
            d.append(["-", ac])
            continue

        # Insert cells from b

        if nbcs == 1:
            # Cell ac maps to a single cell
            pass
        else:
            # Cell ac maps to a single cell
            pass

    return ac2bc, bc2ac, ac2nbcs, bc2nacs


"""
Cells always have:

    "cell_type"
    "metadata"
    "source"

Cell type is either markdown or code:

{
"cell_type" : "markdown",
"metadata" : {},
"source" : "[multi-line *markdown*]",
}

{
  "cell_type" : "code",
  "execution_count": 1, # integer or null
  "metadata" : {
      "collapsed" : True, # whether the output of the cell is collapsed
      "autoscroll": False, # any of true, false or "auto"
  },
  "source" : "[some multi-line code]",
  "outputs": [{
      # list of output dicts (described below)
      "output_type": "stream",
      ...
  }],
}
"""


def diff_cells_linebased(cells_a, cells_b):
    """Compute diff of two cell lists.

    This version first flattens all source lines and then
    does a linebased diff, reconstructing cells afterwards.

    FIXME: Finish this concept? Does it have merit?
    """

    # FIXME: Handle new and deleted cells
    # FIXME: Handle cell_type
    # FIXME: Handle metadata (reuse diff_metadata here)
    # FIXME: Handle execution_count (always change to None?)
    # FIXME: Handle outputs (initial solution: reuse diff_metadata)

    diff = []

    # Extract all source lines from input cells as
    # flat lists with some index tracking data
    lines_a, cell_offsets_a, origin_cell_numbers_a = extract_source_lines(cells_a)
    lines_b, cell_offsets_b, origin_cell_numbers_b = extract_source_lines(cells_b)

    # Perform a regular line diff on the combined sources of all input cells
    line_diff = diff_lines(lines_a, lines_b)
    line_diff = decompress_diff(line_diff)

    # Build arrays with which line number each line moves to or comes from
    a2b, b2a = build_line_to_line_number_mapping(lines_a, lines_b, line_diff)

    # Build arrays with which cell number each line moves to or comes from
    a2bc, b2ac = build_line_to_cell_number_mapping(a2b, b2a, origin_cell_numbers_a, origin_cell_numbers_b)

    '''
    # Build mappings to see where lines originate and end up
    prev_line_a = -1
    prev_cell_a = -1
    prev_line_b = -1
    prev_cell_b = -1
    for s in line_diff:
        act = s[0]

        # Backtrack which cells and local lines the diff lines correspond to
        line_number_a = s[1]
        cell_number_a = origin_cell_numbers_a[line_number_a]
        local_line_number_a = line_number_a - cell_offsets_a[cell_number_a]
        if act != '-':
            line_number_b = s[2]
            cell_number_b = origin_cell_numbers_b[line_number_b]
            local_line_number_b = line_number_b - cell_offsets_b[cell_number_b]

        # At this point we know that we want to keep
        # cells in range(prev_cell_a+1, cell_number_a)
        # TODO: Do something about that? Or use include_equals in diff_lines call?

        # Translate line diff action to cell diff action
        if act == '-':
            # Delete line from cell
            # TODO: Figure out when to delete cell itself
            t = ['-', [cell_number_a, local_line_number_a]]
        elif act == '+':
            # TODO: Figure out when to add new cell
            # Add line to cell
            #value = s[2]
            t = ['+', [cell_number_a, local_line_number_a], [cell_number_b, local_line_number_b]]
        elif act == '!':
            # FIXME:
            value = s[2]
            t = ['!', [cell_number_a, local_line_number_a], [cell_number_b, local_line_number_b]]
        else:
            raise RuntimeError("Invalid diff action {}.".format(act))

        # TODO: How to handle this?
        diff.append(t)

        # Adding to diff list for each cell in a: this approach doesn't deal with cell insertion
        #if cell_number_a > prev_cell_a:
        #    assert cell_number_a not in cdiff
        #    cdiff[cell_number_a] = []
        #cdiff[cell_number_a].append(t)

        # Keep track of the last cell and line we handled in a and b
        prev_line_a = line_number_a
        prev_cell_a = cell_number_a
        if act != '-':
            prev_line_b = line_number_b
            prev_cell_b = cell_number_b
    '''

    return diff
