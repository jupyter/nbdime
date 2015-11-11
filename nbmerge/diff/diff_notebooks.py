"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.

FIXME: Define and document diff format.
"""

__all__ = ["diff_notebooks", "patch_notebook", "diff_cells", "patch_cells"]

import copy

from .diff_metadata import diff_metadata, patch_metadata


def extract_source_lines(cells):
    lines = []
    cell_offsets = []
    origin_cell_numbers = []
    for i, cell in enumerate(cells):
        # Get source as a list of single-line strings without newlines
        source = cell["source"]
        if isinstance(source, str):
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

def diff_cells(cells_a, cells_b):
    """Return a list of transformations to transform notebook cells cells_a into notebook cells cells_b.

    Each transformation is on the format:
    FIXME: Define and document diff format.
    """

    # FIXME: Handle new and deleted cells
    # FIXME: Handle cell_type
    # FIXME: Handle metadata (reuse diff_metadata here)
    # FIXME: Handle execution_count (always change to None?)
    # FIXME: Handle outputs (initial solution: reuse diff_metadata)

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

    # Goal pseudo-diff:
    """
    # Delete a cell:
    ['-', cellindex]
    # Delete all outputs from a cell:
    ['-', [cellindex, "outputs"]]
    # Delete a particular output from a cell:
    ['-', [cellindex, "outputs", outputindex]]
    # Modify cell source:
    ['!', [cellindex, "source"], ]
    """

    diff = []

    # Extract all source lines from input cells as
    # flat lists with some index tracking data
    lines_a, cell_offsets_a, origin_cell_numbers_a = extract_source_lines(cells_a)
    lines_b, cell_offsets_b, origin_cell_numbers_b = extract_source_lines(cells_b)

    # Perform a regular line diff on the combined sources of all input cells
    line_diff = diff_lines(lines_a, lines_b)

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

    return diff

"""
Cells list diff format:
diff = [ # List of transformations on the format:
  ["-", cell_number],             # delete cell at cell_number
  ["+", cell_number, newcell],    # insert newcell before cell_number
  ["!", cell_number, celldiff],   # patch cell at cell_number
]
"""

"""
Single cell diff format:
diff = [ # List of transformations on the format:
  ["-", cell_number],             # delete cell at cell_number
  ["+", cell_number, newcell],    # insert newcell before cell_number
  ["!", cell_number, celldiff],   # patch cell at cell_number
]
"""

def patch_cell(cell, diff):
    # Copy cell
    newcell = cell.copy()
    del newcell["source"]
    newcell = copy.deepcopy(newcell)

    # Patch source lines
    newsource = patch_lines(cell["source"], diff["source"])
    newcell["source"] = newsource

    return newcell

def patch_cells(cells, diff):
    newcells = []

    prev_cell_number = -1
    for s in diff:
        act = s[0]
        cell_number = s[1]

        # Keep cells not mentioned in diff
        keepcells = cells[prev_cell_number+1: cell_number]
        newcells.extend(copy.deepcopy(cell) for cell in keepcells)
        prev_cell_number = cell_number

        if act == '-':
            # Delete cell (just incrementing this to avoid keeping in the next iteration)
            prev_cell_number += 1
        elif act == '+':
            # Insert cell
            cell = copy.deepcopy(s[2]) # FIXME: Store full cell in s[2]?
            newcells.append(cell)
        elif act == '!':
            # Modify cell
            cell_diff = s[2] # FIXME: Store single cell patch in s[2]?
            cell = patch_cell(cells[cell_number], cell_diff) # FIXME: Implement this function
            newcells.append(cell)
        else:
            raise RuntimeError("Invalid diff action {}.".format(act))

    # Keep cells not mentioned in diff
    keepcells = cells[prev_cell_number+1: len(cells)]
    newcells.extend(copy.deepcopy(cell) for cell in keepcells)

    return newcells

def diff_notebooks(nba, nbb):
    """Return a diff structure representing the transformations to transform notebook nba into notebook nbb.

    The format of this
    """
    mdiff = diff_metadata(nba["metadata"], nbb["metadata"])
    cdiff = diff_cells(nba["cells"], nbb["cells"])
    diff = {
        "metadata_diff": mdiff,
        "cells_diff": cdiff,
    }
    return diff

def patch_notebook(nb, diff):
    nb = copy.deepcopy(nb)

    # Document the format we're assuming here (TODO: Get numbers 4,0 from some config)
    # The diff only makes sense in the context of
    # the nbformat we've used internally.
    # To apply the diff to the original notebook,
    # it must be converted to this format before patching.
    assert nb["nbformat"] == 4
    assert nb["nbformat_minor"] == 0

    # Patch metadata
    nb["metadata"] = patch_metadata(nb["metadata"], diff["metadata_diff"])

    # Patch cells
    nb["cells"] = patch_cells(nb["cells"], diff["cells_diff"])

    return nb
