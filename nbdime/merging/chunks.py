# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from ..diff_format import DiffOp, SequenceDiffBuilder


def __unused__get_diff_range(diffs, i):
    "Returns diff entry and range j..k which this diff affects, i.e. base[j:k] is affected."
    e = diffs[i]
    j = e.key
    if e.op == DiffOp.PATCH:
        k = j + 1
    elif e.op == DiffOp.ADDRANGE:
        k = j
    elif e.op == DiffOp.REMOVERANGE:
        k = j + e.length
    else:
        raise ValueError("Unexpected diff op {}".format(e.op))
    return e, j, k


def get_section_boundaries(diffs):
    boundaries = set()
    for e in diffs:
        j = e.key
        boundaries.add(j)
        if e.op == DiffOp.ADDRANGE:
            pass
        elif e.op == DiffOp.REMOVERANGE:
            k = j + e.length
            boundaries.add(k)
        elif e.op == DiffOp.PATCH:
            k = j + 1
            boundaries.add(k)
    return boundaries


def split_diffs_on_boundaries(diffs, boundaries):
    newdiffs = SequenceDiffBuilder()
    assert isinstance(boundaries, list), 'boundaries argument should be a list'

    # Next relevant boundary index
    b = 0

    for e in diffs:
        if e.op in (DiffOp.ADDRANGE, DiffOp.PATCH):
            # Nothing to split
            newdiffs.append(e)
        elif e.op == DiffOp.REMOVERANGE:
            # Skip boundaries smaller than key
            while boundaries[b] < e.key:
                b += 1

            # key should be included in the boundaries
            assert boundaries[b] == e.key, 'key not found in boundaries'

            # Add diff entries for each interval between boundaries up to k
            while b < len(boundaries)-1 and boundaries[b + 1] <= e.key + e.length:
                newdiffs.removerange(boundaries[b], boundaries[b + 1] - boundaries[b])
                b += 1
        else:
            raise ValueError("Unhandled diff entry op {}.".format(e.op))

    return newdiffs.validated()


def make_chunks(boundaries, diffs):
    """Make list of chunks on the form (j, k, diffs0, diffs1, ..., diffsN),
    where `j` and `k` are line numbers in the base, and the `diffsX`
    entries are subsets from `diffs` that are part of the chunk.

    Because the diff entries have been split on the union of
    begin/end boundaries of all diff entries, the keys of
    diff entries on each side will always match a boundary
    exactly. The only situation where multiple diff entries
    on one side matches a boundary is when add/remove or
    add/patch pairs occur, i.e. when inserting something
    just before an item that is removed or modified.
    """
    i_diffs = [0] * len(diffs)
    chunks = []
    nb = len(boundaries)
    for i in range(nb):
        # Find span of next chunk
        j = boundaries[i]
        k = boundaries[i+1] if i < nb-1 else j
        # Collect diff entries from each side
        # starting at beginning of this chunk
        sub_diffs = []
        for m, d in enumerate(diffs):
            dis = []
            while i_diffs[m] < len(d) and d[i_diffs[m]].key == j:
                dis += [d[i_diffs[m]]]
                i_diffs[m] += 1
            sub_diffs.append(dis)
        # Add non-empty chunks
        if j < k or any(sub_diffs):
            chunks.append((j, k) + tuple(sub_diffs))
    return chunks


def make_merge_chunks(base, *diffs, **kwargs):
    """Return list of chunks (i, j, d0, d1, ..., dn) where dX are
    lists of diff entries affecting the range base[i:j].

    If d0 and d1 are both empty the chunk is not modified.

    Includes full range 0:len(base).

    Each diff list contains either 0, 1, or 2 entries,
    in case of 2 entries the first will be an insert
    at i (the beginning of the range) and the other a
    removerange or patch covering the full range i:j.
    """
    if kwargs.get("single_item"):
        # Split diff on single items such that no chunk or
        # diff entry covers more than one base item
        boundaries = list(range(len(base)+1))
    else:
        # Split diffs on union of diff entry boundaries such that
        # no diff entry overlaps with more than one other entry.
        # Including 0,N makes loop over chunks cleaner.
        boundaries = set((0, len(base)))
        for d in diffs:
            boundaries |= get_section_boundaries(d)
        boundaries = sorted(boundaries)

    split_diffs = [split_diffs_on_boundaries(d, boundaries) for d in diffs]

    # Make list of chunks on the form (j, k, diffs)
    chunks = make_chunks(boundaries, split_diffs)

    # Some sanity checking
    if base or split_diffs:
        assert chunks, 'no merge chunks produced'
        assert chunks[0][0] == 0, 'invalid range start of first merge chunk'
        assert chunks[-1][1] == len(base), 'invalid range end of final merge chunk'

    return chunks


def chunk_typename(diffs):
    """For the diffs of a chunk, return string representations of its type.

    Returns a two-tuple of strings.
     - The first string contains zero or more characters 'a' and/or 'A', where
       'a' signifies a dict 'add' operation, and 'A' signifies a sequence
       'addrange' operation.
    - The second string contains zero or more characters 'P', 'R', 'r',
      and/or 'c': 'P': patch, 'R': removerange, 'r': remove, 'c': replace

    For a proper chunk, each string should have either 0 or 1 character each,
    but this function will not perform any checks.
    """
    aname = ""
    pname = ""
    for e in diffs:
        if e.op == DiffOp.ADDRANGE:
            aname += "A"
        elif e.op == DiffOp.ADD:
            aname += "a"
        elif e.op == DiffOp.PATCH:
            pname += "P"
        elif e.op == DiffOp.REMOVERANGE:
            pname += "R"
        elif e.op == DiffOp.REMOVE:
            pname += "r"
        elif e.op == DiffOp.REPLACE:
            pname += "c"
    return aname, pname
