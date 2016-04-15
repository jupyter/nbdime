# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range

from ..diff_format import DiffOp, SequenceDiffBuilder


def __unused__get_diff_range(diffs, i):
    "Returns diff entry and range j..k which this diff affects, i.e. base[j:k] is affected."
    assert i < len(diffs)
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
    assert isinstance(boundaries, list)

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
            assert boundaries[b] == e.key

            # Add diff entries for each interval between boundaries up to k
            while b < len(boundaries)-1 and boundaries[b + 1] <= e.key + e.length:
                newdiffs.removerange(boundaries[b], boundaries[b + 1] - boundaries[b])
                b += 1
        else:
            raise ValueError("Unhandled diff entry op {}.".format(e.op))

    return newdiffs.validated()


def make_chunks(boundaries, diff0, diff1):
    """Make list of chunks on the form (j, k, diffs0, diffs1).

    Because the diff entries have been split on the union of
    begin/end boundaries of all diff entries, the keys of
    diff entries on each side will always match a boundary
    exactly. The only situation where multiple diff entries
    on one side matches a boundary is when add/remove or
    add/patch pairs occur, i.e. when inserting something
    just before an item that is removed or modified.
    """
    i0 = 0
    i1 = 0
    chunks = []
    nb = len(boundaries)
    for i in range(nb):
        # Find span of next chunk
        j = boundaries[i]
        k = boundaries[i+1] if i < nb-1 else j
        # Collect diff entries from each side
        # starting at beginning of this chunk
        d0 = ()
        while i0 < len(diff0) and diff0[i0].key == j:
            d0 += (diff0[i0],)
            i0 += 1
        d1 = ()
        while i1 < len(diff1) and diff1[i1].key == j:
            d1 += (diff1[i1],)
            i1 += 1
        # Add non-empty chunks
        if j < k or d0 or d1:
            chunks.append((j, k, d0, d1))
    return chunks


def make_merge_chunks(base, base_local_diff, base_remote_diff):
    """Return list of chunks (i,j,d0,d1) where d0 and d1 are 
    lists of diff entries affecting the range base[i:j].

    If d0 and d1 are both empty the chunk is not modified.

    Includes full range 0:len(base).

    Each d0,d1 list contain either 0, 1, or 2 entries,
    in case of 2 entries the first will be an insert
    at i (the beginning of the range) and the other a
    removerange or patch covering the full range i:j.
    """
    # Split diffs on union of diff entry boundaries such that
    # no diff entry overlaps with more than one other entry.
    # Including 0,N makes loop over chunks cleaner.
    boundaries = sorted(set((0,len(base)))
                        | get_section_boundaries(base_local_diff)
                        | get_section_boundaries(base_remote_diff))
    diff0 = split_diffs_on_boundaries(base_local_diff, boundaries)
    diff1 = split_diffs_on_boundaries(base_remote_diff, boundaries)

    # Make list of chunks on the form (j, k, diffs0, diffs1)
    chunks = make_chunks(boundaries, diff0, diff1)

    # Some sanity checking
    if base or diff0 or diff1:
        assert chunks
        assert chunks[0][0] == 0
        assert chunks[-1][1] == len(base)

    return chunks
