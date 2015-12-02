# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from six import string_types
from six.moves import xrange as range

import nbformat

from ..diffing import deep_diff

# Sentinel to allow None value
Missing = object()


# TODO: Use this format in diffs directly?
def to_dict_diff(ld):
    dd = {}
    for e in ld:
        if len(e) == 2:
            dd[e[1]] = [e[0]]
        elif len(e) == 3:
            dd[e[1]] = [e[0], e[2]]
        else:
            error("Invalid diff format.")
    return dd


def conflict(basevalue, localvalue, remotevalue, bl_diff, br_diff):
    # TODO: Define conflicts format
    if basevalue is Missing:
        basevalue = None
    if localvalue is Missing:
        localvalue = None
    if remotevalue is Missing:
        remotevalue = None
    #return [basevalue, localvalue, remotevalue, bl_diff, br_diff]
    return [basevalue, localvalue, remotevalue]


def _check_actions(la, ra, bv):
    if la == "+" or ra == "+":
        # Inserted both places (inserting only on one side should never happen with a shared base)
        assert la == "+" and ra == "+"
        assert bv is Missing
    else:
        # Patched or replaced both places
        assert la in (":", "!") and ra in (":", "!")


def dict_diff_entry_to_patch_entry(e):
    if e[0] == "!":
        return e
    if e[0] == "-":
        return {key:"-"}


def merge_dict_items(bv, lv, rv, ld, rd):
    # Switch on diff actions
    if ld[0] == "-" or rd[0] == "-":
        if ld[0] == "-" and rd[0] == "-":
            # (4) Removed in both local and remote
            me = None
            co = None
        else:
            # (5) Conflict: removed one place and edited another
            me = None
            co = conflict(bv, lv, rv, ld, rd) # (ld, rd) contains one of (lv, rv) in this case
    else:
        # Asserts for valid combinations of ld[0] and rd[0]
        _check_actions(ld[0], rd[0], bv)

        # It doesn't matter if values are inserted, replaced,
        # or patched if the end result is equal
        if lv == rv: # ***
            # TODO: We will want to automatically handle some differences
            # like execution count for notebooks. Just adding a custom
            # compare instead of == in here (***) won't cut it, as we want to
            # create a merged value as well.  For the execution count we
            # could just remove them before merging and set all to None
            # afterwards. But there are probably some more intricate cases.
            me = lv
            co = None
        else:
            # At this point, we know that remote and local actions are
            # not no-ops or deletions, and the resulting values differ.
            # New values should also differ from base value here:
            assert bv != lv
            assert bv != rv

            # Get subpatches if already computed
            lp = ld[1] if ld[0] == "!" else None
            rp = rd[1] if rd[0] == "!" else None

            # Recursively attempt to merge lv and rv if possible
            recurse_types = string_types + (list, dict)
            if isinstance(lv, recurse_types) and type(lv) == type(rv):
                me, co = merge(bv, lv, rv, lp, rp)
            else:
                # This code contains lots of corner cases, so using
                # asserts here to rule out cases that don't make sense
                # and check my understanding against examples we come
                # up with later
                assert ld[0] in (":", "+") and ld[1] == lv
                assert rd[0] in (":", "+") and rd[1] == rv
                # Automatic conflict when types are different and not dict/list/string
                me = None
                co = conflict(bv, lv, rv, ld, rd)
    return me, co


def merge_dicts(base, local, remote, base_local_diff=None, base_remote_diff=None):
    """Perform a three-way merge.

    Returns (merged, conflicts), where merged is the dict resulting
    from the merge process without any conflicting changes, and conflicts
    is on the format {key:(basevalue, localvalue, remotevalue)}.
    """
    if base is Missing:
        base = {}
    assert isinstance(base, dict) and isinstance(local, dict) and isinstance(remote, dict)

    # Diffing base->{local|remote}
    if base_local_diff is None:
        base_local_diff = deep_diff(base, local)
    if base_remote_diff is None:
        base_remote_diff = deep_diff(base, remote)

    # Converting to dict-based diff format for dicts for convenience
    base_local_diff = to_dict_diff(base_local_diff)
    base_remote_diff = to_dict_diff(base_remote_diff)


    # FIXME: The diff recursion here is inconsistent, passing only a
    # diff entry below and expecting a full diff above.


    # Summary of diff entry cases with (#) references to below code
    # r\l | N/A   -   +   :   !
    # ----|----------------------
    # N/A | (1)  (2)---------(2)
    #  -  | (3)  (4) (5)-----(5)
    #  +  |  |   (5)
    #  :  |  |    |     (6)
    #  !  | (3)  (5)

    # Get diff keys
    bldkeys = set(base_local_diff.keys())
    brdkeys = set(base_remote_diff.keys())
    dkeys = bldkeys | brdkeys

    # (1) Just use base for all keys with no change
    merged = {key: base[key] for key in set(base.keys()) - dkeys}
    conflicts = {}

    # (2) Next apply one-sided diffs, i.e. no conflicts
    for key in bldkeys - brdkeys:
        # Just use local value or remove
        if base_local_diff[key][0] != "-":
            merged[key] = local[key]
    # (3)
    for key in brdkeys - bldkeys:
        # Just use remote value or remove
        if base_remote_diff[key][0] != "-":
            merged[key] = remote[key]

    # (4) (5) (6)
    # Then we have the potentially conflicting changes
    for key in brdkeys & bldkeys:
        # Get diffs
        ld = base_local_diff[key]
        rd = base_remote_diff[key]

        # Get values
        bv = base.get(key, Missing)
        lv = local.get(key, Missing)
        rv = remote.get(key, Missing)

        # Merge this item independently
        me, co = merge_dict_items(bv, lv, rv, ld, rd)

        # Insert merge result and/or conflict
        if me is not None:
            merged[key] = me
        if co:
            conflicts[key] = co

    return merged, conflicts


def get_deleted_indices(diff):
    deleted = set()
    for e in diff:
        if e[0] == "-":
            deleted.add(e[1])
        elif e[0] == "--":
            deleted.update(e[1] + i for i in range(e[2]))
    return deleted


def merge_lists(base, local, remote, base_local_diff=None, base_remote_diff=None):
    """Perform a three-way merge of two lists.

    Returns (merged, conflicts), FIXME define format of returned values here.

    FIXME: This is a very naive algorithm producing a highly suboptimal
    merge, mainly to have a starting point of the discussion and for myself
    to get a feeling for the difficulties.
    """
    assert False, "This function is under construction and heavily broken at the moment."

    if base is Missing:
        base = []
    assert isinstance(base, list) and isinstance(local, list) and isinstance(remote, list)

    # Diffing base->{local|remote}
    if base_local_diff is None:
        base_local_diff = deep_diff(base, local)
    if base_remote_diff is None:
        base_remote_diff = deep_diff(base, remote)


    # Compute the diff between the base->local and base->remote diffs
    #diffs_diff = diff_sequences(base_local_diff, base_remote_diff)
    # TODO: This will be much cleaner if the diffs are single-item only.


    # Build sets of deleted indices on each side
    local_deleted = get_deleted_indices(base_local_diff)
    remote_deleted = get_deleted_indices(base_local_diff)

    # Get non-deletion diff entries only
    local_diff = [e for e in base_local_diff if e[0] not in ("-", "--")]
    remote_diff = [e for e in base_remote_diff if e[0] not in ("-", "--")]

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
                merged_diff.append(["-", i])
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
            # FIXME: Inserting both won't even work for "!" or ":", only for "+"
            assert le[1] == "+" and re[1] == "+"
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
    return merged, conflicts


def merge_strings(base, local, remote, base_local_diff=None, base_remote_diff=None):
    if base is Missing:
        base = u""
    assert isinstance(base, string_types) and isinstance(local, string_types) and isinstance(remote, string_types)
    me, co = merge_lists(list(base), list(local), list(remote), base_local_diff, base_remote_diff)
    # FIXME: Convert to string compatible format
    merged = u"".join(me)
    conflicts = co
    return merged, conflicts


def merge(base, local, remote, base_local_diff=None, base_remote_diff=None):
    if isinstance(base, dict):
        assert isinstance(local, dict) and isinstance(remote, dict)
        return merge_dicts(base, local, remote, base_local_diff, base_remote_diff)
    elif isinstance(base, list):
        assert isinstance(local, list) and isinstance(remote, list)
        return merge_lists(base, local, remote, base_local_diff, base_remote_diff)
    elif isinstance(base, string_types):
        assert isinstance(local, string_types) and isinstance(remote, string_types)
        return merge_strings(base, local, remote, base_local_diff, base_remote_diff)
    else:
        error("Cannot handle merge of types {}, {}, {}.".format(type(base), type(local), type(remote)))


def merge_notebooks(base, local, remote):
    # FIXME: Implement notebook aware merge
    merged, conflicts = merge(base, local, remote)
    return nbformat.from_dict(merged), conflicts
