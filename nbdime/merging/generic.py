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


insertitem = namedtuple("insertitem", ("index", "value"))


def _split_list_diff(diff, size):
    """Splits a sequence diff based on ops.

    Returns lists (deleted, patched, inserts), where

      deleted[i] = boolean: item i is deleted
      patched[i] = None or diff if item i is patched
      inserts = list of block inserts on the form [[index0, values0], ..., [indexn, valuesn]]

    """
    deleted = [False]*size
    patched = [None]*size
    inserts = []
    for e in diff:
        op = e.op
        if op == Diff.ADDRANGE:
            inserts.append(insertitem(e.key, e.valuelist))
        elif op == Diff.REMOVERANGE:
            for i in range(e.length):
                deleted[e.key + i] = True
        elif op == Diff.PATCH:
            patched[e.key] = e.diff
        else:
            raise ValueError("Invalid diff op {}.".format(e.op))
    return deleted, patched, inserts


def interleave_inserts(local_inserts, remote_inserts):
    # [ (index0, values0), (index1, values1) ]
    empty = [0, [], 0, 0]
    inserts = [copy.deepcopy(empty)]

    l = list(local_inserts)
    r = list(remote_inserts)
    li = 0
    ri = 0
    while li < len(l) or ri < len(r):
        # NB! The code below defines that local inserts
        # are inserted before remote change when index is equal,
        # and that when inserts are made both locally and remote
        # before the same base line, the values are concatenated
        # without considering whether they represent the same change
        # or not. It is possible that checking for duplicate inserts
        # is better, but we need to think this through carefully and
        # investigate what other tools do. At least this naive
        # approach doesn't drop any data.
        if li < len(l) and (ri >= len(r) or l[li].index <= r[ri].index):
            index, values = l[li]
            li += 1
            lskip = len(values)
            rskip = 0
        else:
            index, values = r[ri]
            ri += 1
            lskip = 0
            rskip = len(values)

        if inserts[-1][0] == index:
            # Join inserts at the same base index into one block
            inserts[-1][1].extend(values)
            inserts[-1][2] += lskip
            inserts[-1][3] += rskip
        else:
            # Add new block insert (rebuilding list here to use extend above)
            item = [index, list(values), lskip, rskip]
            inserts.append(item)

    # Remove empty insert items (can this happen more than the initial dummy item?)
    inserts = [item for item in inserts if item != empty]
    return inserts


def _old_merge_lists(base, local, remote, base_local_diff, base_remote_diff):
    """Perform a three-way merge of lists. See docstring of merge."""
    assert isinstance(base, list) and isinstance(local, list) and isinstance(remote, list)

    # Split diffs into different representations
    local_deleted, local_patched, local_inserts = _split_list_diff(base_local_diff, len(base))
    remote_deleted, remote_patched, remote_inserts = _split_list_diff(base_remote_diff, len(base))
    inserts = interleave_inserts(local_inserts, remote_inserts)

    # Add a dummy insert at end to make loop below handle final stretch after last actual insert
    inserts.append([len(base), [], 0, 0])

    # Interleave changes that local and remote agrees on in a merged object
    merged = []

    # Data structures for storing conflicts
    local_conflict_diff = SequenceDiff()
    remote_conflict_diff = SequenceDiff()

    # Offsets or number of items consumed from base, local, remote
    boffset = 0
    loffset = 0
    roffset = 0

    for index, values, lskip, rskip in inserts:
        # 1) consume base[boffset:index]
        for i in range(boffset, index):
            # Bools meaning: local delete, remote deleted, local patched, remote patched
            ld = local_deleted[i]
            rd = remote_deleted[i]
            lp = local_patched[i] is not None
            rp = remote_patched[i] is not None

            # Split the search space: have deletion of this line occurred on at least one side?
            if ld or rd:
                if lp:
                    # Conflict: Deleted remote, patched local
                    # NB! Note the use of j, index into merged, in the conflict diff!
                    j = len(merged)
                    merged.append(base[i])
                    local_conflict_diff.patch(j, local_patched[i])
                    remote_conflict_diff.removerange(j, 1)
                elif rp:
                    # Conflict: Deleted local, patched remote
                    # NB! Note the use of j, index into merged, in the conflict diff!
                    j = len(merged)
                    merged.append(base[i])
                    local_conflict_diff.removerange(j, 1)
                    remote_conflict_diff.patch(j, remote_patched[i])
                else:
                    # Not patched on alternate side, so delete it by just skipping value
                    pass
            else:
                # At this point we know no deletion has occured
                if lp and rp:
                    # Patched on both sides, recurse
                    me, lco, rco = _merge(base[i], local[i+loffset], remote[i+roffset], local_patched[i], remote_patched[i])
                    # NB! Note the use of j, index into merged, in the conflict diff!
                    j = len(merged)
                    merged.append(me)
                    if lco or rco:
                        assert lco and rco
                        local_conflict_diff.patch(j, lco)
                        remote_conflict_diff.patch(j, rco)
                elif lp:
                    if DEBUGGING:
                        # This assert is expensive and must not be enabled in release mode
                        assert local[i+loffset] == patch(base[i], local_patched[i].diff)
                    # Patched on local side only
                    merged.append(local[i+loffset])
                elif rp:
                    if DEBUGGING:
                        # This assert is expensive and must not be enabled in release mode
                        assert remote[i+roffset] == patch(base[i], remote_patched[i].diff)
                    # Patched on remote side only
                    merged.append(remote[i+loffset])
                else:
                    # No deletion, no patching, keep value
                    merged.append(base[i])
        # Start at index next time
        boffset = index

        # 2) insert next range of values before index and skip values in local and remote
        merged.extend(values)
        loffset += lskip
        roffset += rskip

    return merged, local_conflict_diff.diff, remote_conflict_diff.diff  # XXX


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
    b = 0
    for i in range(len(diffs)):
        e = diffs[i]
        j = e.key

        # Skip boundaries smaller than j
        while b < len(boundaries) and boundaries[b] < j:
            b += 1

        if b > len(boundaries) or e.op in (Diff.ADDRANGE, Diff.PATCH):
            # No boundaries left or no diff range to split
            newdiffs.append(e)
        elif e.op == Diff.REMOVERANGE:
            # Find end of diff range
            k = j + e.length

            # Split on boundaries smaller than k
            while b < len(boundaries) and boundaries[b] < k:
                newdiffs.removerange(j, boundaries[b])
                j = boundaries[b]
                b += 1

            # Add remaining diff
            if j < k:
                newdiffs.removerange(j, k)
        else:
            raise ValueError("Unhandled diff entry op {}.".format(e.op))

    return newdiffs.diff


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

    def _apply_diff(e, base, merged):
        # Apply diff entry
        j = e.key
        if e.op == Diff.PATCH:
            assert j < len(base)
            # Patch this entry. Since j < j_other
            merged.append(patch(base[j], e.diff))
            #assert len(merged) - 1 == j + merged_offset  # Not quite sure if this check is correct?
            offset = 0
        elif e.op == Diff.ADDRANGE:
            assert j <= len(base)
            # Add new values
            merged.extend(e.valuelist)
            offset = len(e.valuelist)
        elif e.op == Diff.REMOVERANGE:
            assert j < len(base)
            # Represent skipping of values base[j:j+e.length]
            offset = -e.length
        else:
            raise ValueError("Unexpected diff op {}".format(e.op))
        return offset

    # Split diffs on union of diff entry boundaries such that
    # no diff entry overlaps with more than one other entry
    boundaries = sorted(get_section_boundaries(base_local_diff) | get_section_boundaries(base_remote_diff))
    diff0 = split_diffs_on_boundaries(base_local_diff, boundaries)
    diff1 = split_diffs_on_boundaries(base_remote_diff, boundaries)

    e0 = None
    e1 = None
    i0 = 0
    i1 = 0
    n0 = len(diff0)
    n1 = len(diff1)
    while i0 < n0 and i1 < n1:
        e0, j0, k0 = get_diff_range(diff0, i0)
        e1, j1, k1 = get_diff_range(diff1, i1)

        # At the end of one or both diffs, nothing more to resolve
        if e0 is None or e1 is None:
            break

        if k1 < j0:
            # Remote change does not overlap with local change
            merged_offset += _apply_diff(e1, base, merged)
            i1 += 1
        elif k0 < j1:
            # Local change does not overlap with remote change
            merged_offset += _apply_diff(e0, base, merged)
            i0 += 1
        else:
            # The diffs e0 and e1 are overlapping and thus in (possible) conflict.

            # FIXME: What about the next diff entry?
            # Possible cases still colliding:
            # del base[j:j+n]; base.insert(j, localvalues)  # local diffs
            # del base[j:j+n]; base.insert(j, remotevalues) # remote diffs

            """
remove and patch may not overlap!
local: remove 1..4 -> remove 1..2, remove 3..3, remove 4..4
remote: remove 1..2, patch 3
->
remove 1..2 agreed upon
remove 3 conflicts with patch 3
remove 4 single-sided

x        foo()  x
x        bar()  x
bling()  ting() x
tang()   tang() x

results in partial with conflicts:

bling()  ting()  x

actually this is what git gives:

>>>>>>>
bling()
tang()
=======
<<<<<<<
"""            
            # given abcd:
            # delete b, insert x before b: axcd
            # delete b, insert x before d: acxd

            # Figure out if they are a false conflict, i.e. if they result in the same
            false_conflict = (e0 == e1)  # TODO: Is this check robust?
            if false_conflict:
                # Apply e0 or e1, doesn't matter
                merged_offset += _apply_diff(e1, base, merged)
            else:
                # Keep diffs as conflicts
                local_conflict_diff.append(offset_op(e0, merged_offset))
                remote_conflict_diff.append(offset_op(e1, merged_offset))

            # Skip to the next diff on both sides
            i0 += 1
            i1 += 1

    # Apply final diffs from one of the sides if any
    assert not (i0 < n0 and i1 < n1)
    for i in range(i0, n0):
        merged_offset += _apply_diff(diff0[i], base, merged)
    for i in range(i1, n1):
        merged_offset += _apply_diff(diff1[i], base, merged)

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
