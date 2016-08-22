# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types, text_type
from six.moves import xrange as range
import copy

from ..diffing import diff
from ..diff_format import (DiffOp, as_dict_based_diff, op_removerange,
                           op_remove, op_patch, op_replace, op_addrange)
from .chunks import make_merge_chunks
from ..patching import patch


# Set to true to enable some expensive debugging assertions
DEBUGGING = 0

# Sentinel to allow None value
Missing = object()

collection_types = string_types + (list, dict)


class MergeDecision(dict):
    """For internal usage in nbdime library.

    Minimal class providing attribute access to merge decision keys.

    Tip: If performance dictates, we can easily replace this
    with a namedtuple during processing of diffs and convert
    to dicts before any json conversions.
    """

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            return self.__getattribute__(name)
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class MergeDecisionBuilder(object):
    def __init__(self):
        self.decisions = []

    def validated(self, base):
        return sorted(self.decisions, key=_sort_key, reverse=True)

    def add_decision(self, path, action, local_diff, remote_diff,
                     conflict=False, **kwargs):
        if isinstance(path, list):
            path = tuple(path)
        else:
            assert isinstance(path, tuple)
        if local_diff is not None:
            if isinstance(local_diff, tuple):
                local_diff = list(local_diff)
            elif not isinstance(local_diff, list):
                local_diff = [local_diff]
        if remote_diff is not None:
            if isinstance(remote_diff, tuple):
                remote_diff = list(remote_diff)
            elif not isinstance(remote_diff, list):
                remote_diff = [remote_diff]
        custom_diff = kwargs.pop("custom_diff", None)
        if custom_diff is not None:
            if isinstance(custom_diff, tuple):
                custom_diff = list(custom_diff)
            elif not isinstance(custom_diff, list):
                custom_diff = [custom_diff]
        path, (local_diff, remote_diff, custom_diff) = \
            ensure_common_path(path, [local_diff, remote_diff, custom_diff])
        if custom_diff is not None:
            kwargs["custom_diff"] = custom_diff

        self.decisions.append(MergeDecision(
            common_path=path,
            conflict=conflict,
            action=action,
            local_diff=local_diff,
            remote_diff=remote_diff,
            **kwargs
            ))

    def keep(self, path, key, local_diff, remote_diff):
        self.add_decision(
            path=path,
            action="base",
            local_diff=local_diff,
            remote_diff=remote_diff
        )

    def keep_chunk(self, path, local_diff, remote_diff):
        self.keep(path, local_diff, remote_diff)

    def onesided(self, path, local_diff, remote_diff):
        assert local_diff or remote_diff
        assert not (local_diff and remote_diff)
        if local_diff:
            action = "local"
        elif remote_diff:
            action = "remote"
        self.add_decision(
            path=path,
            action=action,
            local_diff=local_diff,
            remote_diff=remote_diff,
            )

    def onesided_chunk(self, path, local_diff, remote_diff):
        self.onesided(path, local_diff, remote_diff)

    def local_then_remote(self, path, local_diff, remote_diff,
                          conflict=False):
        assert local_diff and remote_diff
        assert local_diff != remote_diff
        action = "local_then_remote"
        self.add_decision(
            path=path,
            conflict=conflict,
            action=action,
            local_diff=local_diff,
            remote_diff=remote_diff
            )

    def agreement(self, path, local_diff, remote_diff):
        assert local_diff and remote_diff
        assert local_diff == remote_diff
        self.add_decision(
            path=path,
            action="either",
            local_diff=local_diff,
            remote_diff=remote_diff,
            )

    def agreement_chunk(self, path, local_diff, remote_diff):
        self.agreement(path, local_diff, remote_diff)

    def conflict(self, path, local_diff, remote_diff):
        assert local_diff and remote_diff
        assert local_diff != remote_diff
        action = "base"
        self.add_decision(
            path=path,
            conflict=True,
            action=action,
            local_diff=local_diff,
            remote_diff=remote_diff,
            )

    def conflict_chunk(self, path, local_diff, remote_diff):
        self.conflict(path, local_diff, remote_diff)


def ensure_common_path(path, diffs):
    """Resolves common paths in a list of diffs.

    If a local and a remote diff both patch a key "a", this will return the
    common path ("a",), and the inner diffs of the patch operations. Works
    recursively, so a common chain of patches will be resolved as well.
    """
    assert isinstance(path, (tuple, list))
    popped = _pop_path(diffs)
    while popped:
        path = path + (popped["key"],)
        diffs = popped["diffs"]
        popped = _pop_path(diffs)
    return path, diffs


def _pop_path(diffs):
    key = None
    popped_diffs = []
    for d in diffs:
        # Empty diffs can be skipped
        if d is None or len(d) == 0:
            popped_diffs.append(None)
            continue
        # Check that we have only one op, which is a patch op
        if len(d) != 1 or d[0].op != DiffOp.PATCH:
            return
        # Ensure all present diffs have the same key
        if key is None:
            key = d[0].key
        elif key != d[0].key:
            return
        # Ensure the sub diffs of all ops are suitable as outer layer
        # if d[0].diff.length > 1:
        #    return
        popped_diffs.append(d[0].diff)
    if key is None:
        return
    return {'key': key, 'diffs': popped_diffs}


def push_path(path, diffs):
    for key in path:
        diffs = [op_patch(key, diffs)]
    return diffs


def split_string_path(base, path):
    """Prevent paths from pointing to specific string lines.

    Check if path points to a specific line in a string, if so, split off
    index.

    Returns a tuple of path and any line key.
    """
    for i in range(len(path)):
        if isinstance(base, string_types):
            return path[:i], path[i:]
        base = base[path[i]]
    return path, ()


def pop_patch_decision(decision):
    diffs = [decision.local_diff, decision.remote_diff]
    if decision.action == "custom":
        diffs.append(decision.custom_diff)
    popped = _pop_path(diffs)
    if popped is None:
        raise ValueError("Cannot pop patch decision for: " + str(decision))
    ret = MergeDecision(
        common_path=decision.common_path + (popped["key"],),
        local_diff=popped["diffs"][0],
        remote_diff=popped["diffs"][1],
        action=decision.action,
        conflict=decision.conflict)
    if decision.action == "custom":
        ret.custom_diff = popped["diffs"][2]
    return ret


def pop_all_patch_decisions(decision):
    try:
        while 1:
            decision = pop_patch_decision(decision)
    except ValueError as e:
        if not str(e).startswith("Cannot pop patch decision for: "):
            raise e
    return decision


def push_patch_decision(decision, prefix):
    """Move a path prefix in a merge decision from `common_path` to the diffs.

    This is done by wrapping the diffs in nested patch ops.
    """
    dec = copy.copy(decision)
    # We need to start with inner most key to nest correctly, so reverse:
    for key in reversed(prefix):
        if len(dec.common_path) == 0:
            raise ValueError(
                "Cannot remove key from empty decision path: %s, %s" %
                (key, dec))
        assert dec.common_path[-1] == key, "Key %s not at end of %s" % (
            key, dec.common_path)
        dec.common_path = dec.common_path[:-1]  # pop key
        dec.local_diff = [op_patch(key, dec.local_diff)]
        dec.remote_diff = [op_patch(key, dec.remote_diff)]
        if dec.action == "custom":
            dec.custom_diff = [op_patch(key, dec.custom_diff)]
    return dec


def _sort_key(k):
    """Sort key for common paths. Ensures the correct order for processing,
without having to care about offsetting indices.

Heavily inspired by the natsort package:

Copyright (c) 2012-2016 Seth M. Morton

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    ret = []
    for s in k.common_path:

        s = (s if isinstance(s, (int, text_type)) else s.decode())

        if isinstance(s, text_type) and s.isnumeric() or isinstance(s, int):
            ret.append(('', -int(s)))
        else:
            ret.append((s,))
    return ret


def make_cleared_value(value):
    "Make a new 'cleared' value of the right type."
    if isinstance(value, list):
        # Clearing e.g. an outputs list means setting it to an empty list
        return []
    elif isinstance(value, dict):
        # Clearing e.g. a metadata dict means setting it to an empty dict
        return {}
    elif isinstance(value, string_types):
        # Clearing e.g. a source string means setting it to an empty string
        return ""
    else:
        # Clearing anything else (atomic values) means setting it to None
        return None


# =============================================================================
#
# Decision-making code follows
#
# =============================================================================


def _merge_dicts(base, local_diff, remote_diff, path, decisions):
    """Perform a three-way merge of dicts. See docstring of merge."""
    assert isinstance(base, dict)

    # Converting to dict-based diff format for dicts for convenience
    # This step will be unnecessary if we change the diff format to work this
    # way always
    local_diff = as_dict_based_diff(local_diff)
    remote_diff = as_dict_based_diff(remote_diff)

    # Summary of diff entry cases with (#) references to below code
    # r\l | N/A   -   +   :   !
    # ----|----------------------
    # N/A | (1)  (2)---------(2)
    #  -  | (3)  (4) (5)-----(5)
    #  +  |  |   (5) (6) (5) (5)
    #  :  |  |    |  (5) (7) (5)
    #  !  | (3)  (5) (5  (5) (8)

    # Get diff keys
    bldkeys = set(local_diff.keys())
    brdkeys = set(remote_diff.keys())
    dkeys = bldkeys | brdkeys

    # (1) Use base values for all keys with no change
    for key in sorted(set(base.keys()) - dkeys):
        pass

    # (2)-(3) Apply one-sided diffs
    for key in sorted(bldkeys ^ brdkeys):
        decisions.onesided(path,
                           local_diff.get(key),
                           remote_diff.get(key))

    # (4) (5) (6) (7) (8)
    # Then we have the potentially conflicting changes
    for key in sorted(brdkeys & bldkeys):
        # Get diff entries for this key (we know both sides have an
        # entry here because all other cases are covered above)
        ld = local_diff[key]
        rd = remote_diff[key]

        # Get values (using Missing as a sentinel to allow None as a value)
        bv = base.get(key, Missing)

        # Switch on diff ops
        lop = ld.op
        rop = rd.op
        if lop != rop:
            # Note that this means the below cases always have the same op
            # (5) Conflict: removed one place and edited another, or edited in
            #     different ways
            decisions.conflict(path, ld, rd)
        elif lop == DiffOp.REMOVE:
            # (4) Removed in both local and remote, just don't add it to merge
            #     result
            decisions.agreement(path, ld, rd)
        elif lop in (DiffOp.ADD, DiffOp.REPLACE, DiffOp.PATCH) and ld == rd:
            # If inserting/replacing/patching produces the same value, just use
            # it
            decisions.agreement(path, ld, rd)
        elif lop == DiffOp.ADD:
            # (6) Insert in both local and remote, values are different
            # This can possibly be resolved by recursion, but leave that to
            # autoresolve
            decisions.conflict(path, ld, rd)
        elif lop == DiffOp.REPLACE:
            # (7) Replace in both local and remote, values are different,
            #     record a conflict against original base value
            decisions.conflict(path, ld, rd)
        elif lop == DiffOp.PATCH:
            # (8) Patch on both local and remote, values are different
            # Patches produce different values, try merging the substructures
            # (a patch command only occurs when the type is a collection, so we
            # can safely recurse here and know we won't encounter e.g. an int)
            _merge(bv, ld.diff, rd.diff, path + (key,), decisions)
        else:
            raise ValueError("Invalid diff ops {} and {}.".format(lop, rop))


def _split_addrange_on_equality(key, local, remote, path, decisions):
    # Here, we need to check for identical inserts, as those are the
    # only entries that need to be aligned
    # FIXME: Use concept of longest common subsequence, instead of fifo
    taken_local = 0
    taken_remote = 0
    seqlen_identical = 0
    for li, lv in enumerate(local):
        if lv in remote[taken_remote:]:
            i = remote.index(lv)
            if seqlen_identical > 0:
                # We're continuing a sequence of identical insertions
                pass
            elif taken_local < li or taken_remote < i:
                # We're starting a new sequence of identical insertions
                # and have a preceding unmatched sequence to add
                ldiff = None
                rdiff = None
                if taken_local < li:
                    ldiff = [op_addrange(key, local[taken_local:li])]
                    taken_local = li + 1
                if taken_remote < i:
                    rdiff = [op_addrange(key, remote[taken_remote:i])]
                    taken_remote = i + 1
                if ldiff is None:
                    decisions.onesided_chunk(path, ldiff, rdiff)
                elif rdiff is None:
                    decisions.onesided_chunk(path, ldiff, rdiff)
                else:
                    decisions.conflict_chunk(path, ldiff, rdiff)
            # Add to matched sequence
            seqlen_identical += 1

        elif seqlen_identical > 0:
            # We finished a sequence of identical insertions
            assert seqlen_identical == li - taken_local
            ri = taken_remote + seqlen_identical
            decisions.agreement_chunk(
                path,
                [op_addrange(key, local[taken_local:li])],
                [op_addrange(key, remote[taken_remote:ri])])
            seqlen_identical = 0
            taken_local = li + 1
            taken_remote = i + 1
    # Finished loop, add any remaining sequences
    if seqlen_identical > 0:
        # Identical sequence remaining
        endl = taken_local + seqlen_identical
        endr = taken_remote + seqlen_identical
        decisions.agreement_chunk(
            path,
            [op_addrange(key, local[taken_local:endl])],
            [op_addrange(key, remote[taken_remote:endr])])
        taken_local = endl
        taken_remote = endr
    if (len(local) > taken_local or len(remote) > taken_remote):
        # Have a final stretch of non-equal inserts
        ldiff = None
        rdiff = None
        if taken_local < len(local):
            ldiff = [op_addrange(key, local[taken_local:])]
        if taken_remote < len(remote):
            rdiff = [op_addrange(key, remote[taken_remote:])]
        if ldiff is None:
            decisions.onesided_chunk(path, ldiff, rdiff)
        elif rdiff is None:
            decisions.onesided_chunk(path, ldiff, rdiff)
        else:
            decisions.conflict_chunk(path, ldiff, rdiff)


def _merge_lists(base, local_diff, remote_diff, path, decisions):
    """Perform a three-way merge of lists. See docstring of merge."""
    assert isinstance(base, list)

    # Split up and combine diffs into chunks
    # format: [(begin, end, localdiffs, remotediffs)]
    chunks = make_merge_chunks(base, local_diff, remote_diff)

    # Loop over chunks of base[j:k], grouping insertion at j into
    # the chunk starting with j
    for (j, k, d0, d1) in chunks:
        if not (bool(d0) or bool(d1)):
            # Unmodified chunk
            pass   # No-op

        elif not (bool(d0) and bool(d1)):
            # One-sided modification of chunk
            decisions.onesided_chunk(path, d0, d1)

        elif d0 == d1:
            # Exactly the same modifications
            decisions.agreement_chunk(path, d0, d1)

            # FIXME: do the above two cases fully cover what the below one did?
        # elif bool(d0) != bool(d1) or (d0 == d1):  # d0 xor d1 or d0 == d1
        #     # One-sided modification of chunk (or exactly the same modifications)
        #     d = d0 or d1  # Pick the non-empty one
        #     # Apply diff entries (either just one or an add + remove or patch)
        #     for e in d:
        #         assert j == e.key
        #         if e.op == DiffOp.PATCH:
        #             assert j < len(base)
        #             merged.append(patch(base[j], e.diff))
        #         elif e.op == DiffOp.ADDRANGE:
        #             assert j <= len(base)
        #             merged.extend(e.valuelist)
        #             merged_offset += len(e.valuelist)
        #         elif e.op == DiffOp.REMOVERANGE:
        #             assert j < len(base)
        #             merged_offset -= e.length
        #         else:
        #             raise ValueError("Unexpected diff op {}".format(e.op))
        #     if (all(e.op == DiffOp.ADDRANGE for e in d0) and
        #         all(e.op == DiffOp.ADDRANGE for e in d1)):
        #         merged.extend(base[j:k])
        elif (len(d0) == len(d1) == 1 and
                d0[0].op == d1[0].op == DiffOp.PATCH and
                d0[0].key == d1[0].key):
            key = d0[0].key
            bv = base[key]
            _merge(bv, d0[0].diff, d1[0].diff,
                   path + (key,), decisions)
        elif len(d0) >= 1 and len(d1) >= 1:
            # Several special cases need to checked for sequentially
            # (may be combination)
            if d0[0] == d1[0]:
                # First op matches on both sides
                decisions.agreement_chunk(path, [d0[0]], [d1[0]])
            elif (d0[0].op == d1[0].op == DiffOp.ADDRANGE and
                    d0[0].key == d1[0].key):
                # Both first ops are insertions, check for identical insertions
                # on both sides
                _split_addrange_on_equality(
                    d0[0].key, d0[0].valuelist, d1[0].valuelist,
                    path, decisions)
            else:
                decisions.conflict_chunk(path, [d0[0]], [d1[0]])

            if len(d0) == len(d1) == 1:
                pass
            elif len(d0) == 1:
                decisions.conflict_chunk(path, None, [d1[1]])
            elif len(d1) == 1:
                decisions.conflict_chunk(path, [d0[1]], None)
            # After previous checks, we know d0 and d1 are both length 2
            elif d0[1] == d1[1]:
                # Insert + patch/remove on both sides, with last ops matching
                # (identical)
                decisions.agreement_chunk(path, [d0[1]], [d1[1]])
            elif (d0[1].op == d1[1].op == DiffOp.PATCH and
                    d0[1].key == d1[1].key):
                # Second ops are both patch ops, recurse
                key = d0[1].key
                bv = base[key]
                _merge(bv, d0[1].diff, d1[1].diff,
                       path + (key,), decisions)
            else:
                raise ValueError("Invalid diff list")

        else:
            # Two-sided modification, i.e. a conflict.
            # It's possible that something more clever can be done here to reduce
            # the number of conflicts. For now we leave this up to the autoresolve
            # code and manual conflict resolution.
            decisions.conflict_chunk(path, d0, d1)


def _merge_strings(base, local_diff, remote_diff,
                   path, decisions):
    """Perform a three-way merge of strings. See docstring of merge."""
    assert isinstance(base, string_types)

    # This functions uses a (static) state variable to track recusrion.
    # The first time it is called, will be with base as a (potentially)
    # multi-line string. We then split this string on line endings, and merge
    # it as a list of lines (giving line-based chunking). However, there if
    # there are conflicting edits (patches) of a line, we will re-enter this
    # function, at which point we simply mark it as a conflict on the parent
    # level (conflicted lines)

    if _merge_strings.recursion:
        # base is a single line with differing edits. We could merge as list of
        # characters, but this is unreliable, and will conflict with line-based
        # chunking.

        # Mark as a conflict on parent (line):
        k = path[-1]
        decisions.conflict(path[:-1],
                           [op_patch(k, local_diff)],
                           [op_patch(k, remote_diff)])
        _merge_strings.recursion = False
    else:
        # Merge lines as lists
        _merge_strings.recursion = True
        base = base.splitlines(True)

        _merge_lists(
            base, local_diff, remote_diff, path, decisions)

_merge_strings.recursion = False


def _merge(base, local_diff, remote_diff, path, decisions):
    if isinstance(base, dict):
        return _merge_dicts(
            base, local_diff, remote_diff, path, decisions)
    elif isinstance(base, list):
        return _merge_lists(
            base, local_diff, remote_diff, path, decisions)
    elif isinstance(base, string_types):
        return _merge_strings(
            base, local_diff, remote_diff, path, decisions)
    else:
        raise ValueError("Cannot handle merge of type {}.".format(type(base)))


def decide_merge_with_diff(base, local, remote, local_diff, remote_diff):
    """Do a three-way merge of same-type collections b, l, r with given diffs
    b->l and b->r."""
    path = ()
    decisions = MergeDecisionBuilder()
    _merge(base, local_diff, remote_diff, path,
           decisions)
    return decisions.validated(base)


def decide_merge(base, local, remote):
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

        md - list of merge decisions

    The merge result can be computed by applying the decisions to the base.
    If any decisions have the conflict field set to True, the merge result will
    use the suggested action, which might not always be correct.

    ## Trying to figure out problem with diff vs diff entry in recursion:

    decide_merge(b, l, r) -> compute bld,brd and call _merge
    _merge(b, bld, brd) -> switch on type of b,l,r
    _merge_dicts(b, bld, brd)
    _merge_lists(b, bld, brd)
    _merge_strings(b, bld, brd)

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
        - Patch op is [DiffOp.PATCH, key, subdiff], providing subdiff for both sides, and meaning values exist on both sides.


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
    local_diff = diff(base, local)
    remote_diff = diff(base, remote)
    return decide_merge_with_diff(base, local, remote, local_diff, remote_diff)


# =============================================================================
#
# Code for applying decisions:
#
# =============================================================================

def resolve_action(base, decision):
    a = decision.action
    if a == "base":
        return []   # no-op
    elif a in ("local", "either"):
        return copy.copy(decision.local_diff)
    elif a == "remote":
        return copy.copy(decision.remote_diff)
    elif a == "custom":
        return copy.copy(decision.custom_diff)
    elif a == "local_then_remote":
        return decision.local_diff + decision.remote_diff
    elif a == "remote_then_local":
        return decision.remote_diff + decision.local_diff
    elif a == "clear":
        key = None
        for d in decision.local_diff + decision.remote_diff:
            if key:
                assert key == d.key
            else:
                key = d.key
        return [op_replace(key, make_cleared_value(base[key]))]
    elif a == "clear_parent":
        if isinstance(base, dict):
            # Ideally we would do a op_replace on the parent, but this is not
            # easily combined with this method, so simply remove all keys
            return [op_remove(key) for key in base.keys()]
        elif isinstance(base, (list,) + string_types):
            return [op_removerange(0, len(base))]

    else:
        raise NotImplementedError("The action \"%s\" is not defined" % a)



def apply_decisions(base, decisions):
    """Apply a list of merge decisions to base.
    """

    merged = copy.deepcopy(base)
    prev_path = None
    parent = None
    last_key = None
    resolved = None
    diffs = None
    # clear_parent actions should override other decisions on same obj, so
    # we need to track it
    clear_parent_flag = False
    for md in decisions:
        path, line = split_string_path(merged, md.common_path)
        # We patch all decisions with the same path in one op
        if path == prev_path:
            # Same path as previous, collect entry
            if clear_parent_flag:
                # Another entry will clear the parent, all other decisions
                # should be dropped
                pass
            else:
                if md.action == "clear_parent":
                    clear_parent_flag = True
                    # Clear any exisiting decsions!
                    diffs = []
                ad = resolve_action(resolved, md)
                if line:
                    ad = push_path(line, ad)
                diffs.extend(ad)

        else:
            # Different path, start a new collection
            if prev_path is not None:
                # First, apply previous diffs
                if parent is None:
                    # Operations on root create new merged object
                    merged = patch(resolved, diffs)
                else:
                    # If not, overwrite entry in parent (which is an entry in
                    # merged). This is ok, as no paths should point to
                    # subobjects of the patched object
                    parent[last_key] = patch(resolved, diffs)

            prev_path = path
            # Resolve path in base and output
            resolved = merged
            parent = None
            last_key = None
            for key in path:
                parent = resolved
                resolved = resolved[key]   # Should raise if key missing
                last_key = key
            diffs = resolve_action(resolved, md)
            if line:
                diffs = push_path(line, diffs)
            clear_parent_flag = md.action == "clear_parent"
    # Apply the last collection of diffs, if present (same as above)
    if prev_path is not None:
        if parent is None:
            merged = patch(resolved, diffs)
        else:
            parent[last_key] = patch(resolved, diffs)
    return merged
