# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range
import copy
from collections import namedtuple

from ..diffing import diff
from ..diff_format import Diff, SequenceDiff, MappingDiff, as_dict_based_diff
from ..patching import patch


# Set to true to enable some expensive debugging assertions
DEBUGGING = 0

# Sentinel to allow None value
Missing = object()

collection_types = string_types + (list, dict)


def _merge_dicts(base, local, remote, base_local_diff, base_remote_diff):
    """Perform a three-way merge of dicts. See docstring of merge."""
    assert isinstance(base, dict) and isinstance(local, dict) and isinstance(remote, dict)

    # Converting to dict-based diff format for dicts for convenience
    # This step will be unnecessary if we change the diff format to work this way always
    base_local_diff = as_dict_based_diff(base_local_diff)
    base_remote_diff = as_dict_based_diff(base_remote_diff)

    # Summary of diff entry cases with (#) references to below code
    # r\l | N/A   -   +   :   !
    # ----|----------------------
    # N/A | (1)  (2)---------(2)
    #  -  | (3)  (4) (5)-----(5)
    #  +  |  |   (5) (6) (5) (5)
    #  :  |  |    |  (5) (7) (5)
    #  !  | (3)  (5) (5  (5) (8)

    # Get diff keys
    bldkeys = set(base_local_diff.keys())
    brdkeys = set(base_remote_diff.keys())
    dkeys = bldkeys | brdkeys

    # (1) Use base values for all keys with no change
    merged = {key: base[key] for key in set(base.keys()) - dkeys}

    # (2) Apply one-sided local diffs
    for key in bldkeys - brdkeys:
        # Just use local value or remove by not inserting
        op = base_local_diff[key].op
        if op != Diff.REMOVE:
            merged[key] = local[key]

    # (3) Apply one-sided remote diffs
    for key in brdkeys - bldkeys:
        # Just use remote value or remove by not inserting
        op = base_remote_diff[key].op
        if op != Diff.REMOVE:
            merged[key] = remote[key]

    # Data structures for storing conflicts
    local_conflict_diff = MappingDiff()
    remote_conflict_diff = MappingDiff()

    # (4) (5) (6)
    # Then we have the potentially conflicting changes
    for key in brdkeys & bldkeys:
        # Get diff entries for this key (we know both sides have an
        # entry here because all other cases are covered above)
        ld = base_local_diff[key]
        rd = base_remote_diff[key]

        # Get values (using Missing as a sentinel to allow None as a value)
        bv = base.get(key, Missing)
        lv = local.get(key, Missing)
        rv = remote.get(key, Missing)

        # Switch on diff ops
        lop = ld.op
        rop = rd.op
        if lop != rop: # Note that this means the below cases always have the same op
            # (5) Conflict: removed one place and edited another, or edited in different ways
            merged[key] = bv
            local_conflict_diff.append(ld)
            remote_conflict_diff.append(rd)
        elif lop == Diff.REMOVE:
            # (4) Removed in both local and remote, just don't add it to merge result
            pass
        elif lop in (Diff.ADD, Diff.REPLACE, Diff.PATCH) and lv == rv:
            # If inserting/replacing/patching produces the same value, just use it
            merged[key] = lv
        elif lop == Diff.ADD:
            # (6) Insert in both local and remote, values are different
            # Try partially merging the inserted values
            if type(lv) == type(rv) and isinstance(lv, collection_types):
                # Use empty collection of the right type as base
                me, lco, rco = merge(type(lv)(), lv, rv)
                # Insert partially merged result
                merged[key] = me
                # And add patch entries for the conflicting parts
                if lco or rco:
                    assert lco and rco
                    local_conflict_diff.patch(key, lco)
                    remote_conflict_diff.patch(key, rco)
            else:
                # Recursive merge not possible, record conflicting adds (no base value)
                local_conflict_diff.append(ld)
                remote_conflict_diff.append(rd)
        elif lop == Diff.REPLACE:
            # (7) Replace in both local and remote, values are different,
            #     record a conflict against original base value
            merged[key] = bv
            local_conflict_diff.append(ld)
            remote_conflict_diff.append(rd)
        elif lop == Diff.PATCH:
            # (8) Patch on both local and remote, values are different
            # Patches produce different values, try merging the substructures
            # (a patch command only occurs when the type is a collection, so we
            # can safely recurse here and know we won't encounter e.g. an int)
            me, lco, rco = _merge(bv, lv, rv, ld.diff, rd.diff)
            # Insert partially merged result
            merged[key] = me
            # And add patch entries for the conflicting parts
            if lco or rco:
                assert lco and rco
                local_conflict_diff.patch(key, lco)
                remote_conflict_diff.patch(key, rco)
        else:
            raise ValueError("Invalid diff ops {} and {].".format(lop, rop))

    lco = sorted(local_conflict_diff.diff, key=lambda x: x.key)  # XXX
    rco = sorted(remote_conflict_diff.diff, key=lambda x: x.key)  # XXX
    return merged, lco, rco


def get_diff_range(diffs, i):
    "Returns diff entry and range j..k which this diff affects, i.e. base[j:k] is affected."
    assert i < len(diffs)
    e = diffs[i]
    j = e.key
    if e.op == Diff.PATCH:
        k = j + 1
    elif e.op == Diff.ADDRANGE:
        k = j
    elif e.op == Diff.REMOVERANGE:
        k = j + e.length
    else:
        raise ValueError("Unexpected diff op {}".format(e.op))
    return e, j, k


def get_section_boundaries(diffs):
    boundaries = set()
    for e in diffs:
        j = e.key
        boundaries.add(j)
        if e.op == Diff.ADDRANGE:
            pass
        elif e.op == Diff.REMOVERANGE:
            k = j + e.length
            boundaries.add(k)
        elif e.op == Diff.PATCH:
            k = j + 1
            boundaries.add(k)
    return boundaries


def split_diffs_on_boundaries(diffs, boundaries):
    newdiffs = SequenceDiff()
    assert isinstance(boundaries, list)

    # Next relevant boundary index
    b = 0

    for e in diffs:
        if e.op in (Diff.ADDRANGE, Diff.PATCH):
            # Nothing to split
            newdiffs.append(e)
        elif e.op == Diff.REMOVERANGE:
            # Skip boundaries smaller than key
            while boundaries[b] < e.key:
                b += 1

            # key should be included in the boundaries
            assert boundaries[b] == e.key

            # Add diff entries for each interval between boundaries up to k
            while b < len(boundaries)-1 and boundaries[b + 1] <= e.key + e.length:
                newdiffs.removerange(boundaries[b], boundaries[b + 1])
                b += 1
        else:
            raise ValueError("Unhandled diff entry op {}.".format(e.op))

    return newdiffs.diff


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


from nbdime.diff_format import DiffEntry

def offset_op(e, n):
    e = DiffEntry(e)
    e.key += n
    return e


def _merge_lists(base, local, remote, base_local_diff, base_remote_diff):
    """Perform a three-way merge of lists. See docstring of merge."""
    assert isinstance(base, list) and isinstance(local, list) and isinstance(remote, list)

    # Interleave changes that local and remote agrees on in a merged object
    merged = []

    # Data structures for storing conflicts
    local_conflict_diff = SequenceDiff()
    remote_conflict_diff = SequenceDiff()

    # Offset of indices between base and merged
    merged_offset = 0

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

    if 0:
        print()
        print(base)
        print(local)
        print(remote)
        print('\n'.join(map(repr,chunks)))
        print()
        
    # Loop over chunks of base[j:k], grouping insertion at j into
    # the chunk starting with j
    for (j, k, d0, d1) in chunks:
        assert len(merged) == j + merged_offset

        if not (d0 or d1):
            # Unmodified chunk
            merged.extend(base[j:k])

        elif (all(e.op == Diff.ADDRANGE for e in d0) and
              all(e.op == Diff.ADDRANGE for e in d1)):
            # Treating two-sided insertions as non-conflicting.
            # NB! This behaviour is possibly contentious, and if
            # this behaviour is not wanted, this elif block can be deleted.
            # Note that insertions should definitely always be part of 
            # conflict if at the beginning of a patch or removerange,
            # but in this case there are two insertions before a
            # list item that will be kept.
            assert j <= len(base)
            for e in d0 + d1:
                merged.extend(e.valuelist)
                merged_offset += len(e.valuelist)
            merged.extend(base[j:k])

        elif bool(d0) != bool(d1) or (d0 == d1):  # xor
            # One-sided modification of chunk (or exactly the same modifications)
            d = d0 or d1  # Pick the non-empty one
            # Apply diff entries (either just one or an add + remove or patch)
            for e in d:
                assert j == e.key
                if e.op == Diff.PATCH:
                    assert j < len(base)
                    merged.append(patch(base[j], e.diff))
                elif e.op == Diff.ADDRANGE:
                    assert j <= len(base)
                    merged.extend(e.valuelist)
                    merged_offset += len(e.valuelist)
                elif e.op == Diff.REMOVERANGE:
                    assert j < len(base)
                    merged_offset -= e.length
                else:
                    raise ValueError("Unexpected diff op {}".format(e.op))
            if (all(e.op == Diff.ADDRANGE for e in d0) and
                all(e.op == Diff.ADDRANGE for e in d1)):
                merged.extend(base[j:k])

        else:
            # Two-sided modification, i.e. a conflict, keeping diffs with an index offset
            # It's possible that something more clever can be done here to reduce
            # the number of conflicts. For now we leave this up to the autoresolve
            # code and manual conflict resolution.
            merged.extend(base[j:k])
            for e in d0:
                local_conflict_diff.append(offset_op(e, merged_offset))
            for e in d1:
                remote_conflict_diff.append(offset_op(e, merged_offset))

    return merged, local_conflict_diff.diff, remote_conflict_diff.diff  # XXX


def _merge_strings(base, local, remote, base_local_diff, base_remote_diff):
    """Perform a three-way merge of strings. See docstring of merge."""
    assert isinstance(base, string_types) and isinstance(local, string_types) and isinstance(remote, string_types)

    # Merge characters as lists
    me, lco, rco = _merge_lists(list(base), list(local), list(remote), base_local_diff, base_remote_diff)

    # Convert to string compatible format
    merged = "".join(me)

    return merged, lco, rco


def _merge(base, local, remote, base_local_diff, base_remote_diff):
    if not (type(base) == type(local) and type(base) == type(remote)):
        raise ValueError("Expecting matching types, got {}, {}, and {}.".format(
            type(base), type(local), type(remote)))

    if isinstance(base, dict):
        return _merge_dicts(base, local, remote, base_local_diff, base_remote_diff)
    elif isinstance(base, list):
        return _merge_lists(base, local, remote, base_local_diff, base_remote_diff)
    elif isinstance(base, string_types):
        return _merge_strings(base, local, remote, base_local_diff, base_remote_diff)
    else:
        raise ValueError("Cannot handle merge of type {}.".format(type(base)))


def merge_with_diff(base, local, remote, base_local_diff, base_remote_diff):
    """Do a three-way merge of same-type collections b, l, r with given diffs b->l and b->r."""
    return _merge(base, local, remote, base_local_diff, base_remote_diff)


def merge(base, local, remote):
    """Do a three-way merge of same-type collections b, l, r.

    Terminology:

        collection = list | dict | string
        value = int | float | string

        (string is a collection of chars or an atomic value depending on parameters)

        (an alternative way to handle string parameters would be a pre/postprocessing
        splitting/joining of strings into lists of lines, lists of words, lists of chars)

    Input:

        b - base collection
        l - local collection
        r - remote collection
        bld - base-local diff
        brd - base-remote diff

    ### Output:

        ad - agreed upon diff
        cld - part of local diff bld that is in conflict with remote diff brd
        crd - part of remote diff brd that is in conflict with local diff bld

    The merge result can be computed by patching base with the agreed diff ad.
    If the conflict diffs cld and crd are empty, the merge result is final,
    otherwise it is the intermediate agreed upon part.

    Note that the diff indices in the conflict diffs still relate to base,
    and will have to be mapped appropriately to the intermediate merge output.


    ### Alternative output:

        m - merge result (partial, or final if no conflicts)
        cld - part of local diff bld that is in conflict with remote diff brd
        crd - part of remote diff brd that is in conflict with local diff bld

    Note that the diff indices in the conflict diffs here relate to the
    intermediate merge result m, and will have to be mapped appropriately
    to the intermediate merge output.


    ### Combination of the two Output:

        ad - agreed upon diff parts (relating to base)
        m - merge result (partial, or final if no conflicts)
        cld - part of local diff bld that is in conflict with remote diff brd
        crd - part of remote diff brd that is in conflict with local diff bld

    Note that the diff indices in the conflict diffs here relate to the
    intermediate merge result m, and will have to be mapped appropriately
    to the intermediate merge output. Postcondition: m == patch(base, ad).

    Critical question: can we be sure the partial merge result is a valid notebook?

    ## Trying to figure out problem with diff vs diff entry in recursion:

    merge(b, l, r) -> compute bld,brd and call _merge
    _merge(b, l, r, bld, brd) -> switch on type of b,l,r
    merge_dicts(b, l, r, bld, brd)
    merge_lists(b, l, r, bld, brd)
    merge_strings(b, l, r, bld, brd)

    Case: b,l,r are dicts, bld,brd are dict diffs, keys of bld,brd correspond to keys in b,l,r.
    Case: b,l,r are lists, bld,brd are list diffs, indices in bld,brd entries correspond to indices in b(,l,r).

    Case: purely nested dicts of values. Alternatives for each dict key:

        One sided ops always ok:
        N,-
        N,!
        N,:
        N,+
        -,N
        !,N
        :,N
        +,N

        Two sided equal ops ok if argument is the same:
        -,- = ok (agree on delete)
        +,+ = ok if equal inserts, otherwise conflict (two sided insert)
        !,! = ok if equal patches, otherwise conflict (two sided patch)
        :,: = ok if equal replacement value, otherwise conflict (two sided replace)

        Different op always conflicts:
        !,- = conflict (delete and patch)
        -,! = conflict (delete and patch)
        :,- = conflict (delete and replace)
        -,: = conflict (delete and replace)
        :,! = conflict (patch and replace)
        !,: = conflict (patch and replace)

        Conflict situations (symmetric, only listing from one side):
        delete / replace or delete / patch -- manual resolution needed
        replace / replace with different value -- manual resolution needed
        insert / insert with different value -- manual resolution needed - recursion will not have a base value for further merging.
        patch / patch with different diff -- recurse!
        replace / patch -- manual resolution needed, will only happen if collection type changes in replace


        Takeaways:
        - Ensure that diff always uses patch on collections unless the type changes and replace on values.
        - The only recursion will happen on the patch / patch op of equal type collections!
        - Patch op is [Diff.PATCH, key, subdiff], providing subdiff for both sides, and meaning values exist on both sides.


    ## Next trying to figure out list situations:

    Case: purely nested lists of values. Alternatives for each base item:

        One sided ops always ok:
        N,-
        N,+
        N,!

        Delete and patch is a conflict:
        -,! = conflict (delete and patch)

        Two sided equal ops ok if argument is the same:
        -,- = ok (agree on deleting this item)
        -,+ = ok (delete this item and insert new values)
        +,+ = ok (always insert both, or pick one if new values are equal?)
        !,! = ok (recurse)
        !,+ = ok (patch this item and insert new values)

        Conflict situations (symmetric, only listing from one side):
        delete / replace or delete / patch -- manual resolution needed
        replace / replace with different value -- manual resolution needed
        insert / insert with different value -- manual resolution needed - recursion will not have a base value for further merging.
        patch / patch with different diff -- recurse!
        replace / patch -- manual resolution needed, will only happen if collection type changes in replace

    """
    base_local_diff = diff(base, local)
    base_remote_diff = diff(base, remote)
    return merge_with_diff(base, local, remote, base_local_diff, base_remote_diff)
