# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from six import string_types
from six.moves import xrange as range

import nbformat

from ..diffing import deep_diff
from ..dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE

# Sentinel to allow None value
Missing = object()


collection_types = string_types + (list, dict)


# TODO: Use this format in diffs directly?
def to_dict_diff(ld):
    dd = {}
    for e in ld:
        if len(e) == 2:
            dd[e[1]] = [e[0]]
        elif len(e) == 3:
            dd[e[1]] = [e[0], e[2]]
        else:
            raise ValueError("Invalid diff format.")
    return dd


def _merge_dicts(base, local, remote, base_local_diff, base_remote_diff):
    """Perform a three-way merge of dicts

    Returns (merged, conflicts), where merged is the dict resulting
    from the merge process without any conflicting changes, and conflicts
    is on the format {key:(basevalue, localvalue, remotevalue)}.
    """
    assert isinstance(base, dict) and isinstance(local, dict) and isinstance(remote, dict)

    # Converting to dict-based diff format for dicts for convenience
    # This step will be unnecessary if we change the diff format to work this way always
    base_local_diff = to_dict_diff(base_local_diff)
    base_remote_diff = to_dict_diff(base_remote_diff)

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
        if base_local_diff[key][0] != DELETE:
            merged[key] = local[key]

    # (3) Apply one-sided remote diffs
    for key in brdkeys - bldkeys:
        # Just use remote value or remove by not inserting
        if base_remote_diff[key][0] != DELETE:
            merged[key] = remote[key]

    # Data structures for storing conflicts
    local_conflict_diff = {}
    remote_conflict_diff = {}

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

        # Switch on diff actions
        if ld[0] != rd[0]: # Note that this means the below cases always have the same action
            # (5) Conflict: removed one place and edited another, or edited in different ways
            local_conflict_diff[key] = ld
            remote_conflict_diff[key] = rd
        elif ld[0] == DELETE and rd[0] == DELETE:
            # (4) Removed in both local and remote, just don't add it to merge result
            pass
        elif ld[0] in (INSERT, REPLACE, PATCH) and lv == rv:
            # If inserting/replacing/patching produces the same value, just use it
            merged[key] = lv
        elif ld[0] == INSERT:
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
                    local_conflict_diff[key] = [PATCH, lco]
                    remote_conflict_diff[key] = [PATCH, rco]
            else:
                # Recursive merge not possible, record a conflict
                local_conflict_diff[key] = ld
                remote_conflict_diff[key] = rd
        elif ld[0] == REPLACE:
            # (7) Replace in both local and remote, values are different
            local_conflict_diff[key] = ld
            remote_conflict_diff[key] = rd
        elif ld[0] == PATCH:
            # (8) Patch on both local and remote, values are different
            # Patches produce different values, try merging the substructures
            # (a patch command only occurs when the type is a collection, so we
            # can safely recurse here and know we won't encounter e.g. an int)
            me, lco, rco = _merge(bv, lv, rv, ld[1], rd[1])
            # Insert partially merged result
            merged[key] = me
            # And add patch entries for the conflicting parts
            if lco or rco:
                assert lco and rco
                local_conflict_diff[key] = [PATCH, lco]
                remote_conflict_diff[key] = [PATCH, rco]
        else:
            raise ValueError("Invalid diff actions {} and {].".format(ld[0], rd[0]))

    return merged, local_conflict_diff, remote_conflict_diff


def get_deleted_indices(diff):
    deleted = set()
    for e in diff:
        if e[0] == DELETE:
            deleted.add(e[1])
        elif e[0] == SEQDELETE:
            deleted.update(e[1] + i for i in range(e[2]))
    return deleted


def _merge_lists(base, local, remote, base_local_diff=None, base_remote_diff=None):
    """Perform a three-way merge of two lists.

    Returns (merged, conflicts), FIXME define format of returned values here.

    FIXME: This is a very naive algorithm producing a highly suboptimal
    merge, mainly to have a starting point of the discussion and for myself
    to get a feeling for the difficulties.
    """
    assert False, "This function is under construction and heavily broken at the moment."

    assert isinstance(base, list) and isinstance(local, list) and isinstance(remote, list)

    # Data structures for storing conflicts
    local_conflict_diff = []
    remote_conflict_diff = []


    # Compute the diff between the base->local and base->remote diffs
    #diffs_diff = diff_sequences(base_local_diff, base_remote_diff)
    # TODO: This will be much cleaner if the diffs are single-item only.


    # Build sets of deleted indices on each side
    local_deleted = get_deleted_indices(base_local_diff)
    remote_deleted = get_deleted_indices(base_local_diff)

    # Get non-deletion diff entries only
    local_diff = [e for e in base_local_diff if e[0] not in (DELETE, SEQDELETE)]
    remote_diff = [e for e in base_remote_diff if e[0] not in (DELETE, SEQDELETE)]

    # Interleave local and remote diff entries in a merged diff object
    merged_diff = []
    conflicts = [] # FIXME: Format?
    lk = 0
    rk = 0
    lastindex = 0
    while lk < len(local_diff) and rk < len(remote_diff):
        le = local_diff[lk]
        re = remote_diff[rk]
        lindex = le[1]
        rindex = re[1]
        index = min(lindex, rindex)

        # Insert deletions up to (and including) this point
        for i in range(lastindex, index+1): # (+1 for including) # FIXME: include +1 or make it part of conflict resolution?
            ldel = i in local_deleted
            rdel = i in remote_deleted
            if ldel:
                local_deleted.remove(i)
            if rdel:
                remote_deleted.remove(i)
            if ldel or rdel:
                merged_diff.append([DELETE, i])
        lastindex = min(lastindex, index+1) # FIXME: +1 here?

        #
        if lindex < rindex:
            # FIXME: Conflicts if remote_deletes overlap
            merged_diff.append(le)
        elif lindex > rindex:
            # FIXME: Conflicts if local_deletes overlap
            merged_diff.append(re)
        else:
            # FIXME: Create conflict instead of inserting both
            # FIXME: Inserting both won't even work for PATCH or REPLACE, only for INSERT
            assert le[1] == INSERT and re[1] == INSERT
            merged_diff.append(le)
            merged_diff.append(re)

    # Add trailing diff entries, only one of these can be non-empty
    # FIXME: Handle deletion conflicts too here
    merged_diff.extend(local_diff[lk:])
    merged_diff.extend(remote_diff[rk:])

    # Assert that we've inserted all the deletions
    assert not local_deleted
    assert not remote_deleted

    merged = patch(base, merged_diff)
    return merged, local_conflict_diff, remote_conflict_diff


def _merge_strings(base, local, remote, base_local_diff, base_remote_diff):
    assert isinstance(base, string_types) and isinstance(local, string_types) and isinstance(remote, string_types)

    # Merge characters as lists
    me, lco, rco = _merge_lists(list(base), list(local), list(remote), base_local_diff, base_remote_diff)

    # Convert to string compatible format
    merged = u"".join(me)

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

        One sided actions always ok:
        N,-
        N,!
        N,:
        N,+
        -,N
        !,N
        :,N
        +,N

        Two sided equal actions ok if argument is the same:
        -,- = ok (agree on delete)
.        +,+ = ok if equal inserts, otherwise conflict (two sided insert)
.        !,! = ok if equal patches, otherwise conflict (two sided patch)
.        :,: = ok if equal replacement value, otherwise conflict (two sided replace)

        Different action always conflicts:
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
        - The only recursion will happen on the patch / patch action of equal type collections!
        - Patch action is ["!", key, subdiff], providing subdiff for both sides, and meaning values exist on both sides.


    ## Next trying to figure out list situations:

    Case: purely nested lists of values. Alternatives for each base item:

        One sided actions always ok:
        N,-
        N,+
        N,!

        Delete and patch is a conflict:
        -,! = conflict (delete and patch)

        Two sided equal actions ok if argument is the same:
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
    base_local_diff = deep_diff(base, local)
    base_remote_diff = deep_diff(base, remote)
    return _merge(base, local, remote, base_local_diff, base_remote_diff)


def merge_notebooks(base, local, remote):
    # FIXME: Implement notebook aware merge
    merged, conflicts = merge(base, local, remote)
    return nbformat.from_dict(merged), conflicts



"""

nbdiff: nb, nb  -> di

nbmerge: nb, nb, nb -> nb, di, di


diff: obj, obj -> di
merge: obj, obj, obj, di, di -> obj, di, di


"""