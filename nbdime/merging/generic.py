# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range
import copy
from collections import namedtuple

from ..diffing import diff
from ..diff_format import PATCH, ADD, REMOVE, REPLACE, ADDRANGE, REMOVERANGE
from ..diff_format import SequenceDiff, MappingDiff
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
    base_local_diff = {e.key: e for e in base_local_diff}
    base_remote_diff = {e.key: e for e in base_remote_diff}

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
        if op != REMOVE:
            merged[key] = local[key]

    # (3) Apply one-sided remote diffs
    for key in brdkeys - bldkeys:
        # Just use remote value or remove by not inserting
        op = base_remote_diff[key].op
        if op != REMOVE:
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
            local_conflict_diff.append(ld)
            remote_conflict_diff.append(rd)
        elif lop == REMOVE:
            # (4) Removed in both local and remote, just don't add it to merge result
            pass
        elif lop in (ADD, REPLACE, PATCH) and lv == rv:
            # If inserting/replacing/patching produces the same value, just use it
            merged[key] = lv
        elif lop == ADD:
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
                # Recursive merge not possible, record a conflict
                local_conflict_diff.append(ld)
                remote_conflict_diff.append(rd)
        elif lop == REPLACE:
            # (7) Replace in both local and remote, values are different
            local_conflict_diff.append(ld)
            remote_conflict_diff.append(rd)
        elif lop == PATCH:
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
        if op == ADDRANGE:
            inserts.append(insertitem(e.key, e.values))
        elif op == REMOVERANGE:
            for i in range(e.length):
                deleted[e.key + i] = True
        elif op == PATCH:
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


def _merge_lists(base, local, remote, base_local_diff, base_remote_diff):
    """Perform a three-way merge of lists. See docstring of merge."""
    assert isinstance(base, list) and isinstance(local, list) and isinstance(remote, list)

    # Split diffs into different representations
    local_deleted, local_patched, local_inserts = _split_list_diff(base_local_diff, len(base))
    remote_deleted, remote_patched, remote_inserts = _split_list_diff(base_remote_diff, len(base))
    inserts = interleave_inserts(local_inserts, remote_inserts)

    # Add a dummy insert at end to make loop below handle final stretch after last actual insert
    inserts.append([len(base), [], 0, 0])

    # Interleave local and remote diff entries in a merged diff object
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
                    remote_conflict_diff.remove(j, 1)
                elif rp:
                    # Conflict: Deleted local, patched remote
                    # NB! Note the use of j, index into merged, in the conflict diff!
                    j = len(merged)
                    merged.append(base[i])
                    local_conflict_diff.remove(j, 1)
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
        raise ValueError("Expecting matching types, got {}, {}, and {}.".format(type(base), type(local), type(remote)))

    if isinstance(base, dict):
        return _merge_dicts(base, local, remote, base_local_diff, base_remote_diff)
    elif isinstance(base, list):
        return _merge_lists(base, local, remote, base_local_diff, base_remote_diff)
    elif isinstance(base, string_types):
        return _merge_strings(base, local, remote, base_local_diff, base_remote_diff)

    raise ValueError("Cannot handle merge of type {}.".format(type(base)))


def merge(base, local, remote):
    """Do a three-way merge of same-type collections b, l, r.

    Terminology:

        collection = list | dict | string
        value = int | float | string

        (string is a collection of chars or atomic value depending on parameters)

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
.        +,+ = ok if equal inserts, otherwise conflict (two sided insert)
.        !,! = ok if equal patches, otherwise conflict (two sided patch)
.        :,: = ok if equal replacement value, otherwise conflict (two sided replace)

        Different op always conflicts:
        !,- = conflict (delete and patch)
        -,! = conflict (delete and patch)
        :,- = conflict (delete and replace)
        -,: = conflict (delete and replace)
.        :,! = conflict (patch and replace)
.        !,: = conflict (patch and replace)

  ! : + -
! r x x m
: x r x m
+ x x m x
- m m x -

        Conflict situations (symmetric, only listing from one side):
        delete / replace or delete / patch -- manual resolution needed
        replace / replace with different value -- manual resolution needed
        insert / insert with different value -- manual resolution needed - recursion will not have a base value for further merging.
        patch / patch with different diff -- recurse!
        replace / patch -- manual resolution needed, will only happen if collection type changes in replace


        Takeaways:
        - Ensure that diff always uses patch on collections unless the type changes and replace on values.
        - The only recursion will happen on the patch / patch op of equal type collections!
        - Patch op is [PATCH, key, subdiff], providing subdiff for both sides, and meaning values exist on both sides.


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

  ! : + -
! r x x m
: x r x m
+ x x m x
- m m x -

        Conflict situations (symmetric, only listing from one side):
        delete / replace or delete / patch -- manual resolution needed
        replace / replace with different value -- manual resolution needed
        insert / insert with different value -- manual resolution needed - recursion will not have a base value for further merging.
        patch / patch with different diff -- recurse!
        replace / patch -- manual resolution needed, will only happen if collection type changes in replace

    """
    base_local_diff = diff(base, local)
    base_remote_diff = diff(base, remote)
    return _merge(base, local, remote, base_local_diff, base_remote_diff)
