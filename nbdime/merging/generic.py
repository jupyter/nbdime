# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types

from .decisions import MergeDecisionBuilder
from .chunks import make_merge_chunks
from ..diffing import diff
from ..diff_format import (
    DiffOp, ParentDeleted, Missing, as_dict_based_diff, op_patch, op_addrange, op_removerange)
from ..diffing.notebooks import notebook_predicates, notebook_differs
from ..patching import patch
from ..utils import star_path
import nbdime.log


# Set to true to enable some expensive debugging assertions
DEBUGGING = 0


# =============================================================================
#
# Decision-making code follows
#
# =============================================================================


def _merge_dicts(base, local_diff, remote_diff, path, decisions, strategies):
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

    # Get base path for strategy lookup
    spath = star_path(path)

    # (4) (5) (6) (7) (8)
    # Then we have the potentially conflicting changes
    for key in sorted(brdkeys & bldkeys):
        # Get diff entries for this key (we know both sides have an
        # entry here because all other cases are covered above)
        ld = local_diff[key]
        rd = remote_diff[key]

        # Get values (using Missing as a sentinel to allow None as a value)
        bv = base.get(key, Missing)

        # Get strategy for this key
        strategy = strategies.get("/".join((spath, key)))

        """Possible strategies:
             Producing decisions with new values:
                inline-source - callback  (path=/cells/*, key=source)
                inline-attachments - callback  (path=/cells/*, key=attachments)
                inline-outputs - callback  (path=/cells/*, key=outputs)
                record-conflict - callback  (path=/cells/*, path=/, path=/cells/*/outputs/*, key=metadata)
                union - register conflict(?)
             Applicable in decisions.conflict:
                fail - crash and burn
                mergetool - as today, just register conflict
                clear - custom decision to replace value at key on parent path!
                use-local/base/remote - register conflict(?), mark action local/base/remote

# Strategies for handling conflicts
generic_conflict_strategies = (
x    "fail",             # Unexpected: crash and burn in case of conflict

x    "clear",            # Replace value with empty in case of conflict
x    "take-max",         # Take the maximum value in case of conflict

    "inline-source",    # Valid for source only: produce new source with inline diff markers

    "remove",           # Discard value in case of conflict
    "clear-all",        # Discard all values on conflict
    "inline-outputs",   # Valid for outputs only: produce new outputs with inline diff markers

    "record-conflict",  # Valid for metadata only: produce new metadata with conflicts recorded for external inspection

    "mergetool",        # Do not modify decision (but prevent processing at deeper path)

    "union",            # Join values in case of conflict, don't insert new markers
    "use-base",         # Keep base value in case of conflict
    "use-local",        # Use local value in case of conflict
    "use-remote",       # Use remote value in case of conflict
        """

        if ld.op == DiffOp.REMOVE and rd.op == DiffOp.REMOVE:
            # (4) Removed in both local and remote, just don't add it to merge
            #     result
            decisions.agreement(path, ld, rd)
        elif ld.op == DiffOp.REMOVE or rd.op == DiffOp.REMOVE:
            # (5) Conflict: removed one place and edited another
            decisions.conflict(path, ld, rd, strategy=strategy)
        elif ld.op != rd.op:
            # Note that this means the below cases always have the same op
            # (5) Conflict: edited in different ways
            decisions.conflict(path, ld, rd, strategy=strategy)
        elif ld == rd:
            # If inserting/replacing/patching produces the same value, just use
            # it
            decisions.agreement(path, ld, rd)
        elif ld.op == DiffOp.ADD:
            # (6) Insert in both local and remote, values are different
            # This can possibly be resolved by recursion, but leave that to
            # autoresolve
            decisions.conflict(path, ld, rd, strategy=strategy)  # XXX FIXME: consider merging added values
        elif ld.op == DiffOp.REPLACE:
            # (7) Replace in both local and remote, values are different,
            #     record a conflict against original base value
            decisions.conflict(path, ld, rd, strategy=strategy)
        elif ld.op == DiffOp.PATCH:
            # (8) Patch on both local and remote, values are different
            # Patches produce different values, try merging the substructures
            # (a patch command only occurs when the type is a collection, so we
            # can safely recurse here and know we won't encounter e.g. an int)
            _merge(bv, ld.diff, rd.diff, path + (key,), decisions, strategies)  # XXX FIXME: pass parent strategy? push it on strategy stack?
        else:
            raise ValueError("Invalid diff ops {} and {}.".format(ld.op, rd.op))


def _split_addrange(key, local, remote, path):
    """Compares two addrange value lists, and splits decisions on similarity

    Uses diff of value lists to identify which items to align. Identical,
    aligned inserts are decided as in agreement, while inserts that are aligned
    without being identical are treated as conflicts (possibly to be resolved
    by autoresolve). Non-aligned inserts are treated as conflict free,
    one-sided inserts.
    """
    # FIXME: This uses notebook predicates and differs, which
    #        doesn't really belong in a generic merge algorithm...

    # First, find diff between local and remote insertion values.
    # This will align common subsequences according to the similarity
    # measures defined in notebook predicates.
    intermediate_diff = diff(local, remote, path=star_path(path),
                             predicates=notebook_predicates.copy(),
                             differs=notebook_differs.copy())

    # Next, translate the diff into decisions
    decisions = MergeDecisionBuilder()
    taken = 0
    offset = 0  # Offset between diff keys (ref local) and remote
    for i, d in enumerate(intermediate_diff):
        # This should only occur after (*) marked below:
        if d.key < taken:
            continue
        if taken < d.key:
            # No diff, which means elements are inserted on both sides
            overlap = [op_addrange(key, local[taken:d.key])]
            decisions.agreement(path, overlap, overlap)
            taken = d.key

        # Either (1) conflicted, (2) local onesided, or (3) remote onesided
        # First checks whether the next op is a removal on the same key
        # as the current one (i.e. a range substitution).
        if (i + 1 < len(intermediate_diff) and
                intermediate_diff[i+1].op == DiffOp.REMOVERANGE and
                intermediate_diff[i+1].key == d.key):
            # This indicates a non-similar sub-sequence, according
            # to the predicates.
            # (1) Conflicted addition
            local_len = intermediate_diff[i+1].length
            ld = [op_addrange(key, local[d.key:d.key+local_len])]
            rd = [op_addrange(key, d.valuelist)]
            decisions.conflict(path, ld, rd)
            offset += len(d.valuelist) - local_len
            # (*) Here we treat two ops in one go, which we mark
            # by setting taken beyond the key of the next op:
            taken += local_len
        elif d.op == DiffOp.REPLACE:
            # Same as above, but length of one, so simpler
            # (1) Conflict (one element each)
            ld = [op_addrange(key, [local[d.key]])]
            rd = [op_addrange(key, [d.value])]
            decisions.conflict(path, ld, rd)
            taken += 1
        elif d.op in (DiffOp.REMOVE, DiffOp.REMOVERANGE):
            # (2) Local onesided
            if d.op == DiffOp.REMOVE:
                vl = [local[d.key]]
            else:
                vl = local[d.key:d.key + d.length]
            decisions.onesided(path, [op_addrange(key, vl)], None)
            offset -= len(vl)
            taken += len(vl)
        elif d.op in (DiffOp.ADD, DiffOp.ADDRANGE):
            # (3) Remote onesided
            if d.op == DiffOp.ADD:
                vl = [d.value]
            else:
                vl = d.valuelist
            decisions.onesided(path, None, [op_addrange(key, vl)])
            offset += len(vl)
        elif d.op == DiffOp.PATCH:
            # Predicates indicate that local and remote are similar!
            # Mark as conflict, possibly for autoresolve to deal with
            decisions.conflict(path,
                               [op_addrange(key, [local[d.key]])],
                               [op_addrange(key, [remote[d.key + offset]])])
            taken += 1
        else:
            raise ValueError("Invalid diff op: %s" % d.op)

    # We have made at least one split
    if taken < len(local):
        # Have elements that are inserted on both sides
        overlap = [op_addrange(key, local[taken:])]
        decisions.agreement(path, overlap, overlap)
    if len(decisions.decisions) > 1 or not decisions.decisions[0].conflict:
        return decisions.decisions
    else:
        return None


def _merge_concurrent_inserts(base, ldiff, rdiff, path, decisions, strategies):
    """Merge concurrent inserts, optionally with one or more removeranges.

    This method compares the addition/removals on both sides, and splits it
    into individual agreement/onesided/conflict decisions.
    """
    # Assume first ops are always inserts
    assert ldiff[0].op == DiffOp.ADDRANGE and rdiff[0].op == DiffOp.ADDRANGE

    subdec = _split_addrange(ldiff[0].key, ldiff[0].valuelist, rdiff[0].valuelist, path)

    if subdec:
        # We were able to split insertion [+ onesided removal]
        decisions.extend(subdec)

        # Add potential one-sided removal at end
        if len(ldiff) > 1 or len(rdiff) > 1:
            decisions.onesided(path, ldiff[1:], rdiff[1:])
    else:
        # Were not able to infer any additional information,
        # simply add as they are (conflicted).
        decisions.conflict(path, ldiff, rdiff)


def is_diff_all_transients(diff, path, transients):
    # Resolve diff paths and check them vs transients list
    for d in diff:
        # Convert to string to search transients:
        subpath = path + (d.key,)
        if d.op == DiffOp.PATCH:
            # Recurse
            if not is_diff_all_transients(d.diff, subpath, transients):
                return False
        else:
            # Check path vs transients
            if star_path(subpath) not in transients:
                return False
    return True


def chunkname(diffs):
    aname = ""
    pname = ""
    for e in diffs:
        if e.op == DiffOp.ADDRANGE:
            aname += "A"
        elif e.op == DiffOp.REMOVERANGE:
            pname += "R"
        elif e.op == DiffOp.PATCH:
            pname += "P"
    return aname, pname


def _merge_lists(base, local_diff, remote_diff, path, decisions, strategies):
    """Perform a three-way merge of lists. See docstring of merge."""
    assert isinstance(base, list)

    transients = strategies.transients if strategies else {}

    # Split up and combine diffs into chunks
    # format: [(begin, end, localdiffs, remotediffs)]
    chunks = make_merge_chunks(base, local_diff, remote_diff)

    # Loop over chunks of base[j:k], grouping insertion at j into
    # the chunk starting with j
    for (j, k, d0, d1) in chunks:

        laname, lpname = chunkname(d0)
        raname, rpname = chunkname(d1)
        lname = laname + lpname
        rname = raname + rpname
        chunktype = lname + "/" + rname
        achunktype = laname + "/" + raname
        pchunktype = lpname + "/" + rpname
        #allops = "".join(sorted(set(lname + rname)))

        # These are accessed in a lot of different combinations below
        a0 = d0[:-1]  # local addrange (0 or 1)
        p0 = d0[-1:]  # local patch or removerange (0 or 1)
        a1 = d1[:-1]  # remote addrange (0 or 1)
        p1 = d1[-1:]  # remote patch or removerange (0 or 1)

        # More intuitive to read key than j far below
        key = j

        # ... The rest of this function is a big if-elif-elif 'switch'

        # Unmodified chunk
        if chunktype == "/":
            pass   # No-op

        # One-sided modification of chunk
        elif not (bool(d0) and bool(d1)):
            decisions.onesided(path, d0, d1)

        # Exactly the same modifications
        elif d0 == d1:
            decisions.agreement(path, d0, d1)

        # Should always agree above because of chunking
        elif chunktype == "R/R":
            nbdime.log.error("Not expecting conflicting two-sided removal at this point.")

        # Workaround for string merge (FIXME: Make a separate function for string merge)
        elif isinstance(base, string_types) and chunktype == "AP/AP":
            # In these cases, simply merge the As, then consider patches after
            _merge_concurrent_inserts(
                base, a0, a1, path, decisions, strategies)

            # The rest is P/P:
            # For string base, replace patches with add/remove line
            # TODO: This is intended as a short term workaround until
            # more robust chunking of strings are included
            bv = base[key]
            lv = patch(bv, d0[1].diff)
            rv = patch(bv, d1[1].diff)
            if lv == rv:
                # Agreed patch on string
                decisions.agreement(path + (key,),
                    [op_addrange(key, [lv]), op_removerange(key, 1)],
                    [op_addrange(key, [rv]), op_removerange(key, 1)])
            else:
                decisions.conflict(path + (key,),
                    [op_addrange(key, [lv]), op_removerange(key, 1)],
                    [op_addrange(key, [rv]), op_removerange(key, 1)])

        # Patch/remove conflicts (with or without prior insertion)
        elif pchunktype in ("P/P", "P/R", "R/P"):
            # Deal with prior insertion first
            if achunktype == "A/A":
                # In these cases, simply merge the As, then consider patches after
                _merge_concurrent_inserts(base, a0, a1, path, decisions, strategies)
            elif achunktype in ("A/", "/A"):
                # Onesided addition + conflicted patch/remove
                # TODO: Should we mark addition before patch/remove conflicted as well?
                decisions.onesided(path, a0, a1)  # conflict=True)

            # Then deal with patches and/or removals
            if p0 == p1:
                decisions.agreement(path, p0, p1)
            else:
                # XXX Recurse into patches but with parent deletion passed on!!!
                ldiff = p0[0].diff if p0[0].op == DiffOp.PATCH else ParentDeleted
                rdiff = p1[0].diff if p1[0].op == DiffOp.PATCH else ParentDeleted
                thediff = ldiff if rdiff is ParentDeleted else rdiff

                using_inlining_strategy = False  # FIXME XXX

                # If one side is deleted and the other only transients, pick the deletion
                if ldiff is ParentDeleted and is_diff_all_transients(rdiff, path, transients):
                    decisions.local(path, p0, p1)
                elif rdiff is ParentDeleted and is_diff_all_transients(ldiff, path, transients):
                    decisions.remote(path, p0, p1)
                elif using_inlining_strategy:
                    # XXX Check for ParentDeleted in _merge_list/dict/string!
                    # Possible results of a ParentDeleted / patch situation:
                    #   - patch contains only transient changes and can be discarded (generic behaviour)
                    #   - recurse and take ParentDeleted into account, making  (inline behaviour)
                    #   - add conflict decision on parent and leave it at that (mergetool behaviour)
                    _merge(base[key], ldiff, rdiff, path + (key,), decisions, strategies)
                else:
                    # Mergetool behaviour, behaviour when no strategy selected:
                    # just conflicted, no further recursion
                    decisions.conflict(path, p0, p1)

        # Insert before patch or remove: apply both but mark as conflicted
        elif chunktype in ("A/P", "A/R"):
            decisions.local_then_remote(path, d0, d1, conflict=True)
        elif chunktype in ("P/A", "R/A"):
            decisions.remote_then_local(path, d0, d1, conflict=True)

        # Merge insertions from both sides and add onesided patch afterwards
        elif chunktype in ("A/AP", "AP/A"):
            # Not including patches in merging of inserts
            _merge_concurrent_inserts(base, a0, a1, path, decisions, strategies)
            decisions.onesided(path, p0, p1)

        # Identical (ensured by chunking) twosided removal with insertion just before one of them
        elif chunktype in ("AR/R", "R/AR"):
            decisions.onesided(path, a0, a1)
            decisions.agreement(path, p0, p1)
        # Variations of range substitutions
        elif chunktype in "AR/AR":
           # XXX FIXME: Support two-sided removal in _merge_concurrent_inserts, see autoresolve?
           decisions.conflict(path, d0, d1)
        elif chunktype in ("AR/A", "A/AR", "A/A", "AR/AR"):
            # Including removals in merging of inserts
            _merge_concurrent_inserts(base, d0, d1, path, decisions, strategies)

        else:
            assert nbdime.log.error("Unhandled chunk conflict type %s" % (chunktype,))

    # FIXME


def _merge_strings(base, local_diff, remote_diff,
                   path, decisions, strategies):
    """Perform a three-way merge of strings. See docstring of merge."""
    assert isinstance(base, string_types)

    # This functions uses a (static) state variable to track recursion.
    # The first time it is called, base can (potentially) be a
    # multi-line string. If so, we split this string on line endings, and merge
    # it as a list of lines (giving line-based chunking). However, if
    # there are conflicting edits (patches) of a line, we will re-enter this
    # function. If so, we simply mark it as conflicted lines.

    if _merge_strings.recursion:
        # base is a single line with differing edits. We could merge as list of
        # characters, but this is unreliable, and will conflict with line-based
        # chunking.

        # Mark as a conflict on parent (line):
        k = path[-1]
        decisions.conflict(path[:-1],
                           [op_patch(k, local_diff)],
                           [op_patch(k, remote_diff)])
    else:
        # Merge lines as lists
        _merge_strings.recursion = True
        base = base.splitlines(True)

        try:
            _merge_lists(
                base, local_diff, remote_diff, path, decisions, strategies)
        finally:
            _merge_strings.recursion = False

_merge_strings.recursion = False


def _merge(base, local_diff, remote_diff, path, decisions, strategies):
    if isinstance(base, dict):
        return _merge_dicts(
            base, local_diff, remote_diff, path, decisions, strategies)
    elif isinstance(base, list):
        return _merge_lists(
            base, local_diff, remote_diff, path, decisions, strategies)
    elif isinstance(base, string_types):
        return _merge_strings(
            base, local_diff, remote_diff, path, decisions, strategies)
    else:
        raise ValueError("Cannot handle merge of type {}.".format(type(base)))


def decide_merge_with_diff(base, local, remote, local_diff, remote_diff, strategies=None):
    """Do a three-way merge of same-type collections b, l, r with given diffs
    b->l and b->r."""
    if strategies is None:
        strategies = {}
    path = ()
    decisions = MergeDecisionBuilder()
    _merge(base, local_diff, remote_diff, path,
           decisions, strategies)
    return decisions.validated(base)


def decide_merge(base, local, remote, strategies=None):
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
    if strategies is None:
        strategies = {}
    local_diff = diff(base, local)
    remote_diff = diff(base, remote)
    return decide_merge_with_diff(base, local, remote, local_diff, remote_diff, strategies)
