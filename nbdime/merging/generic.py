# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
import copy
from collections import defaultdict

from .decisions import MergeDecisionBuilder
from .chunks import make_merge_chunks
from ..diffing import diff
from ..diff_format import (
    DiffOp, ParentDeleted, Missing, as_dict_based_diff, op_patch, op_addrange, op_removerange, op_add, op_replace)
from ..diffing.notebooks import notebook_predicates, notebook_differs
from ..patching import patch
from ..utils import star_path, join_path
import nbdime.log


# FIXME XXX: Main todos left:
# - implement resolve_* by rewriting other handlers (search for resolve_ and follow FIXME instructions, see resolve_strategy_record_conflicts for example of expected behaviour)
# - implement handling of ParentDeleted cases (see top of _merge_lists and _merge_dicts)
# - _merge_strings is probably broken, test and fix 
# - extend test_merge_notebooks_inline with more tests
# - make existing test suite pass, either by modifying tests or fixing remaining bugs
# - test that this still works with mergetool (it shouldn't need any changes in principle)
# - remove autoresolve.py after checking for anything more we need from there


def is_diff_all_transients(diff, path, transients):
    "Check if all diffs have paths in the transients set."
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


def combine_patches(diffs):
    """Rewrite diffs in canonical form where only one patch
    applies to one key and diff entries are sorted by key."""
    patches = {}
    newdiffs = []
    for d in diffs:
        if d.op == DiffOp.PATCH:
            p = patches.get(d.key)
            if p is None:
                p = op_patch(d.key, combine_patches(d.diff))
                newdiffs.append(p)
                patches[d.key] = p
            else:
                p.diff.extend(combine_patches(d.diff))
        else:
            newdiffs.append(d)
    return sorted(newdiffs, key=lambda x: x.key)



# =============================================================================
#
# Decision-making code follows
#
# =============================================================================

def collect_unresolved_diffs(base_path, unresolved_conflicts):
    # Collect diffs
    local_conflict_diffs = []
    remote_conflict_diffs = []
    for conf in unresolved_conflicts:
        (path, ld, rd, strategy) = conf

        assert isinstance(ld, list)
        assert isinstance(rd, list)

        assert base_path == path[:len(base_path)]
        relative_path = path[len(base_path):]
        assert not relative_path

        for d in ld:
            local_conflict_diffs.append(d)
        for d in rd:
            remote_conflict_diffs.append(d)

    # Combine patches into canonical tree again
    local_conflict_diffs = combine_patches(local_conflict_diffs)
    remote_conflict_diffs = combine_patches(remote_conflict_diffs)
    return local_conflict_diffs, remote_conflict_diffs



def make_inline_source_value(base, local_diff, remote_diff):  # FIXME XXX rewrite and use for resolve_strategy_inline_source
    """Make an inline source from conflicting local and remote diffs"""
    orig = base
    base = base.splitlines(True)

    #base = source string
    # replace = replace line e.key from base with e.value
    # patch = apply e.diff to line e.key from base
    # remove = remove lines e.key from base
    local = patch(orig, local_diff)
    remote = patch(orig, remote_diff)
    begin = 0
    end = len(base)

    inlined = merge_render(base, local, remote)
    inlined = inlined.splitlines(True)

    # Return range to replace with marked up lines
    return begin, end, inlined
def make_inline_source_decision(source, prefix, local_diff, remote_diff):  # FIXME XXX rewrite and use for resolve_strategy_inline_source
    begin, end, inlined = make_inline_source_value(source, local_diff, remote_diff)
    custom_diff = [
        op_addrange(begin, inlined),
        op_removerange(begin, end-begin),
    ]
    return [MergeDecision(
        common_path=prefix,
        action="custom",
        conflict=True,
        local_diff=local_diff,
        remote_diff=remote_diff,
        custom_diff=custom_diff,
    )]
def resolve_strategy_inline_source(base_path, base, unresolved_conflicts, decisions):
    pass # FIXME XXX: Implement by rewriting functions above copied from autoresolve.py, search for resolve_strategy_inline_source above in this file


def resolve_strategy_inline_attachments(base_path, attachments, unresolved_conflicts, decisions):
    local_conflict_diffs, remote_conflict_diffs = collect_unresolved_diffs(base_path, unresolved_conflicts)

    ldiffs_by_key = {d.key: d for d in local_conflict_diffs}
    rdiffs_by_key = {d.key: d for d in remote_conflict_diffs}
    conflict_keys = sorted(set(ldiffs_by_key) | set(rdiffs_by_key))

    for key in conflict_keys:
        # key is the attachment filename
        ld = ldiffs_by_key[key]
        rd = rdiffs_by_key[key]

        if ld.op == DiffOp.REMOVE:
            assert rd.op != DiffOp.REMOVE
            decisions.remote(base_path, ldiffs, rdiffs, conflict=True)
        elif rd.op == DiffOp.REMOVE:
            decisions.local(base_path, ldiffs, rdiffs, conflict=True)
            decisions.custom(base_path, ldiffs, rdiffs, custom_diff, conflict=True)
        else:
            # Not merging attachment contents, but adding attachments
            # with new names LOCAL_oldname and REMOTE_oldname instead.

            base = attachments[key]

            if ld.op == DiffOp.ADD:
                assert rd.op == DiffOp.ADD
                local = ld.value
            elif ld.op == DiffOp.REPLACE:
                local = ld.value
            else:
                assert ld.op == DiffOp.PATCH
                local = patch(base, ld.diff)

            if rd.op == DiffOp.ADD:
                remote = rd.value
            elif rd.op == DiffOp.REPLACE:
                remote = rd.value
            else:
                assert rd.op == DiffOp.PATCH
                remote = patch(base, rd.diff)

            local_name = "LOCAL_" + key
            remote_name = "REMOTE_" + key

            custom_diff = []

            if local_name in attachments:
                nbdime.log.warning("Replacing previous conflicted attachment with filename '{}'".format(local_name))
                custom_diff += [op_replace(local_name, local)]
            else:
                custom_diff += [op_add(local_name, local)]

            if remote_name in attachments:
                nbdime.log.warning("Replacing previous conflicted attachment with filename '{}'".format(remote_name))
                custom_diff += [op_replace(remote_name, remote)]
            else:
                custom_diff += [op_add(remote_name, remote)]

            decisions.custom(base_path, ldiffs, rdiffs, custom_diff, conflict=True)


def output_marker(text):
    return nbformat.v4.new_output("stream", name="stderr", text=text)


def get_outputs_and_note(base, removes, patches):
    if removes:
        note = " <removed>"
        suboutputs = []
    elif patches:
        e, = patches  # 0 or 1 item

        # Collect which mime types are modified
        mkeys = set()
        keys = set()
        for d in e.diff:
            if d.key == "data":
                assert d.op == DiffOp.PATCH
                for f in d.diff:
                    mkeys.add(f.key)
            else:
                keys.add(d.key)
        data = base.get("data")
        if data:
            ukeys = set(data.keys()) - mkeys
        else:
            ukeys = ()

        notes = []
        if mkeys or keys:
            notes.append("modified: {}".format(", ".join(sorted(mkeys))))
        if ukeys:
            notes.append("unchanged: {}".format(", ".join(sorted(ukeys))))
        if notes:
            note = " <" + "; ".join(notes) + ">"
        else:
            note = ""

        suboutputs = [patch(base, e.diff)]
    else:
        note = " <unchanged>"
        suboutputs = [base]
    return suboutputs, note


def make_inline_output_conflict(base_output, local_diff, remote_diff):
    """Make a list of outputs with conflict markers from conflicting
    local and remote diffs applying to a single base_output"""

    # Styling details
    base_title = "base"
    local_title = "local"
    remote_title = "remote"
    marker_size = 7  # default in git
    m0 = "<"*marker_size
    m1 = "|"*marker_size
    m2 = "="*marker_size
    m3 = ">"*marker_size

    # Split diffs by type
    d0 = local_diff
    d1 = remote_diff
    lpatches = [e for e in d0 if e.op == DiffOp.PATCH]
    rpatches = [e for e in d1 if e.op == DiffOp.PATCH]
    linserts = [e for e in d0 if e.op == DiffOp.ADDRANGE]
    rinserts = [e for e in d1 if e.op == DiffOp.ADDRANGE]
    lremoves = [e for e in d0 if e.op == DiffOp.REMOVERANGE]
    rremoves = [e for e in d1 if e.op == DiffOp.REMOVERANGE]
    assert len(lpatches) + len(linserts) + len(lremoves) == len(d0)
    assert len(rpatches) + len(rinserts) + len(rremoves) == len(d1)

    # Collect new outputs with surrounding markers
    outputs = []

    # Collect inserts from both sides separately
    if linserts or rinserts:
        lnote = ""
        loutputs = []
        for e in linserts:  # 0 or 1 item
            loutputs.extend(e.valuelist)
        rnote = ""
        routputs = []
        for e in rinserts:  # 0 or 1 item
            routputs.extend(e.valuelist)

        outputs.append(output_marker("%s %s%s\n" % (m0, local_title, lnote)))
        outputs.extend(loutputs)
        outputs.append(output_marker("%s\n" % (m2,)))
        outputs.extend(routputs)
        outputs.append(output_marker("%s %s%s\n" % (m3, remote_title, rnote)))

    # Keep base output if untouched (only inserts)
    keep_base = not (lremoves or rremoves or lpatches or rpatches)
    if not keep_base:
        assert not (lremoves and lpatches)
        assert not (rremoves and rpatches)
        lnote = ""
        rnote = ""

        # Insert changed output with surrounding markers
        loutputs, lnote = get_outputs_and_note(base_output, lremoves, lpatches)
        routputs, rnote = get_outputs_and_note(base_output, rremoves, rpatches)

        outputs.append(output_marker("%s %s%s\n" % (m0, local_title, lnote)))
        outputs.extend(loutputs)
        outputs.append(output_marker("%s\n" % (m2,)))
        outputs.extend(routputs)
        outputs.append(output_marker("%s %s%s\n" % (m3, remote_title, rnote)))

    # Return marked up output
    return outputs, keep_base


def split_diffs_by_index(diffs):
    """Splits list diffs (removeranges) by index and return
    dict mapping index to list of diff entries affecting that index."""
    diffs_by_index = defaultdict(list)
    for d in diffs:
        if d.op == DiffOp.REMOVERANGE:
            for i in range(d.key, d.key + d.length):
                diffs_by_index[i].append(op_removerange(i, 1))
        else:
            diffs_by_index[d.key].append(d)
    return diffs_by_index


def resolve_strategy_inline_outputs(base_path, outputs, unresolved_conflicts, decisions):
    local_conflict_diffs, remote_conflict_diffs = collect_unresolved_diffs(base_path, unresolved_conflicts)

    ldiffs_by_index = split_diffs_by_index(local_conflict_diffs)
    rdiffs_by_index = split_diffs_by_index(remote_conflict_diffs)
    conflict_indices = sorted(set(ldiffs_by_index) | set(rdiffs_by_index))

    for i in conflict_indices:
        ldiffs = ldiffs_by_index[i]
        rdiffs = rdiffs_by_index[i]

        inlined_conflict, keep_base = make_inline_output_conflict(outputs[i], ldiffs, rdiffs)
        custom_diff = []
        custom_diff += [op_addrange(i, inlined_conflict)]
        if not keep_base:
            custom_diff += [op_removerange(i, 1)]
        decisions.custom(base_path, ldiffs, rdiffs, custom_diff, conflict=True)


def resolve_strategy_record_conflicts(base_path, base, unresolved_conflicts, decisions):
    local_conflict_diffs, remote_conflict_diffs = collect_unresolved_diffs(base_path, unresolved_conflicts)

    # Record remaining conflicts in field nbdime-conflicts
    conflicts_dict = {
        "local_diff": local_conflict_diffs,
        "remote_diff": remote_conflict_diffs,
    }
    if "nbdime-conflicts" in base:
        nbdime.log.warning("Replacing previous nbdime-conflicts field from base notebook.")
        op = op_replace("nbdime-conflicts", conflicts_dict)
    else:
        nbdime.log.warning("Recording unresolved conflicts in {}/nbdime-conflicts.".format(join_path(base_path)))
        op = op_add("nbdime-conflicts", conflicts_dict)
    custom_diff = [op]

    decisions.custom(base_path, local_conflict_diffs, remote_conflict_diffs, custom_diff, conflict=True)


def wrap_subconflicts(key, subconflicts):
    unresolved_conflicts = []
    for conf in subconflicts:
        (path, ld, rd, strategy) = conf
        assert path[-1] == key
        path = path[:-1]
        ld = [op_patch(key, ld)]
        rd = [op_patch(key, rd)]
        unresolved_conflicts.append((path, ld, rd, strategy))
    return unresolved_conflicts


def tryresolve_conflicts(conflicts, decisions):
    unresolved_conflicts = []
    for conf in conflicts:
        (path, ld, rd, strategy) = conf
        # Try to resolve conflict with strategy
        action_taken = decisions.tryresolve(path, ld, rd, strategy=strategy)
        if not action_taken:
            unresolved_conflicts.append(conf)
    return unresolved_conflicts


def _merge_dicts(base, local_diff, remote_diff, path, decisions, strategies):
    """Perform a three-way merge of dicts. See docstring of merge."""
    assert isinstance(base, dict)

    # FIXME XXX Handle if local or remote diff is ParentDeleted

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

    # Get strategy for this dict
    parent_strategy = strategies.get(spath)
    unresolved_conflicts = []
    conflicts = []

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

        if ld.op == DiffOp.REMOVE and rd.op == DiffOp.REMOVE:
            # (4) Removed in both local and remote, just don't add it to merge
            #     result
            decisions.agreement(path, ld, rd)
        elif ld.op == DiffOp.REMOVE or rd.op == DiffOp.REMOVE:
            # (5) Conflict: removed one place and edited another
            conflicts.append((path, [ld], [rd], strategy))
        elif ld.op != rd.op:
            # Note that this means the below cases always have the same op
            # (5) Conflict: edited in different ways
            conflicts.append((path, [ld], [rd], strategy))
        elif ld == rd:
            # If inserting/replacing/patching produces the same value, just use
            # it
            decisions.agreement(path, ld, rd)
        elif ld.op == DiffOp.ADD:
            # (6) Insert in both local and remote, values are different
            # This can possibly be resolved by recursion, but leave that to
            # autoresolve
            # XXX FIXME: consider merging added values
            conflicts.append((path, [ld], [rd], strategy))
        elif ld.op == DiffOp.REPLACE:
            # (7) Replace in both local and remote, values are different,
            #     record a conflict against original base value
            conflicts.append((path, [ld], [rd], strategy))
        elif ld.op == DiffOp.PATCH:
            # (8) Patch on both local and remote, values are different
            # Patches produce different values, try merging the substructures
            # (a patch command only occurs when the type is a collection, so we
            # can safely recurse here and know we won't encounter e.g. an int)
            subconflicts = _merge(bv, ld.diff, rd.diff, path + (key,), decisions, strategies)
            unresolved_conflicts.extend(wrap_subconflicts(key, subconflicts))
        else:
            raise ValueError("Invalid diff ops {} and {}.".format(ld.op, rd.op))

    # Attempt to resolve conflicts that occured at this level
    unresolved_conflicts.extend(tryresolve_conflicts(conflicts, decisions))

    # Resolve remaining conflicts with strategy at this level if any
    if unresolved_conflicts:
        if parent_strategy == "record-conflict":
            # affects conflicts on dicts at /***/metadata or below
            resolve_strategy_record_conflicts(path, base, unresolved_conflicts, decisions)
            unresolved_conflicts = []
        elif parent_strategy == "inline-attachments":
            # affects conflicts on string at /cells/*/attachments or below
            resolve_strategy_inline_attachments(path, base, unresolved_conflicts, decisions)
            unresolved_conflicts = []

    # Return the rest of the conflicts
    return unresolved_conflicts


def _split_addrange(key, local, remote, path, strategies=None):
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

    strategy = strategies.get(star_path(path + (key,)))

    unresolved_conflicts = []

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
            unresolved_conflicts.append((path, ld, rd, strategy))
            offset += len(d.valuelist) - local_len
            # (*) Here we treat two ops in one go, which we mark
            # by setting taken beyond the key of the next op:
            taken += local_len

        elif d.op == DiffOp.REPLACE:
            # Same as above, but length of one, so simpler
            # (1) Conflict (one element each)
            ld = [op_addrange(key, [local[d.key]])]
            rd = [op_addrange(key, [d.value])]
            unresolved_conflicts.append((path, ld, rd, strategy))
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
            unresolved_conflicts.append((path,
                               [op_addrange(key, [local[d.key]])],
                               [op_addrange(key, [remote[d.key + offset]])],
                               strategy))
            taken += 1

        else:
            raise ValueError("Invalid diff op: %s" % d.op)

    # We have made at least one split
    if taken < len(local):
        # Have elements that are inserted on both sides
        overlap = [op_addrange(key, local[taken:])]
        decisions.agreement(path, overlap, overlap)

    # if len(decisions.decisions) > 1 or not decisions.decisions[0].conflict:
    #     return decisions.decisions
    # else:
    #     return None
    return decisions.decisions, unresolved_conflicts


def _merge_concurrent_inserts(base, ldiff, rdiff, path, decisions, strategies=None):
    """Merge concurrent inserts, optionally with one or more removeranges.

    This method compares the addition/removals on both sides, and splits it
    into individual agreement/onesided/conflict decisions.
    """
    # Assume first ops are always inserts
    assert ldiff[0].op == DiffOp.ADDRANGE and rdiff[0].op == DiffOp.ADDRANGE

    unresolved_conflicts = []

    subdec, subconflicts = _split_addrange(ldiff[0].key,
        ldiff[0].valuelist, rdiff[0].valuelist,
        path, strategies=strategies)

    # FIXME XXX: _split_addrange had a very specific return condition, what does it do? Probably need to match behaviour: len(subdec) > 1 or len(subdec) == 1 and subdec[0]
    # if subdec:
    #     for conf in subconflicts:
    #         unresolved_conflicts.append(conf)
    if not subconflicts:

        # We were able to split insertion [+ onesided removal]
        decisions.extend(subdec)

        # Add potential one-sided removal at end
        if len(ldiff) > 1 or len(rdiff) > 1:
            decisions.onesided(path, ldiff[1:], rdiff[1:])
    else:
        # Were not able to infer any additional information,
        # simply add as they are (conflicted).
        strategy = strategies.get(star_path(path + (ldiff[0].key,)))
        unresolved_conflicts.append((path, ldiff, rdiff, strategy))

    return unresolved_conflicts


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

    # FIXME XXX Handle if local or remote diff is ParentDeleted


    transients = strategies.transients if strategies else {}

    # Split up and combine diffs into chunks
    # format: [(begin, end, localdiffs, remotediffs)]
    chunks = make_merge_chunks(base, local_diff, remote_diff)

    # Get base path for strategy lookup
    spath = star_path(path)

    # Get strategy for this dict
    parent_strategy = strategies.get(spath)
    unresolved_conflicts = []
    conflicts = []

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
            subconflicts = _merge_concurrent_inserts(
                base, a0, a1, path, decisions, strategies)
            conflicts.extend(subconflicts)  # FIXME XXX: Wrap or not?
            #conflicts.extend(wrap_subconflicts(key, subconflicts))

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
                unresolved_conflicts.append(
                    (path + (key,),
                    [op_addrange(key, [lv]), op_removerange(key, 1)],
                    [op_addrange(key, [rv]), op_removerange(key, 1)])
                )

        # Patch/remove conflicts (with or without prior insertion)
        elif pchunktype in ("P/P", "P/R", "R/P"):
            # Deal with prior insertion first
            if achunktype == "A/A":
                # In these cases, simply merge the As, then consider patches after
                subconflicts = _merge_concurrent_inserts(base, a0, a1, path, decisions, strategies)
                conflicts.extend(subconflicts)  # FIXME XXX: Wrap or not?
                #conflicts.extend(wrap_subconflicts(key, subconflicts))

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

                # Possible results of a ParentDeleted / patch situation:
                #   - patch contains only transient changes and can be discarded (generic behaviour)
                #   - recurse and take ParentDeleted into account, making custom decisions (inline behaviour)
                #   - add conflict decision on parent and leave it at that (mergetool behaviour)

                if ( (ldiff is ParentDeleted and is_diff_all_transients(rdiff, path, transients))
                    or (rdiff is ParentDeleted and is_diff_all_transients(ldiff, path, transients))):
                    # If one side is deleted and the other only transients,
                    # drop the transient diffs and let parent pick the deletion
                    pass
                elif ldiff is ParentDeleted or rdiff is ParentDeleted:
                    # If one is deleted, no point in recursing?
                    # FIXME XXX: Consider if recursion is still useful to have
                    # strategies applied to subdocuments, followed by a check on subconflicts
                    conflicts.append((path, p0, p1, parent_strategy)) # FIXME XXX Is this the right strategy?
                else:
                    # Otherwise recurse and pass on unresolved conflicts
                    subconflicts = _merge(base[key], ldiff, rdiff, path + (key,), decisions, strategies)
                    unresolved_conflicts.extend(wrap_subconflicts(key, subconflicts))

        # Insert before patch or remove: apply both but mark as conflicted
        elif chunktype in ("A/P", "A/R"):
            decisions.local_then_remote(path, d0, d1, conflict=True)
        elif chunktype in ("P/A", "R/A"):
            decisions.remote_then_local(path, d0, d1, conflict=True)

        # Merge insertions from both sides and add onesided patch afterwards
        elif chunktype in ("A/AP", "AP/A"):
            # Not including patches in merging of inserts
            subconflicts = _merge_concurrent_inserts(base, a0, a1, path, decisions, strategies)
            conflicts.extend(subconflicts)  # FIXME XXX: Wrap or not?
            #conflicts.extend(wrap_subconflicts(key, subconflicts))
            decisions.onesided(path, p0, p1)

        # Variations of range substitutions
        elif chunktype in ("AR/R", "R/AR"):
            # Identical (ensured by chunking) twosided removal with insertion just before one of them
            decisions.onesided(path, a0, a1)
            decisions.agreement(path, p0, p1)
        elif chunktype in "AR/AR":
            # XXX FIXME: Support two-sided removal in _merge_concurrent_inserts, see autoresolve?
            conflicts.append((path, d0, d1, parent_strategy)) # FIXME XXX Is this the right strategy?
        elif chunktype in ("AR/A", "A/AR", "A/A"): #, "AR/AR"):
            # Including removals in merging of inserts
            subconflicts = _merge_concurrent_inserts(base, d0, d1, path, decisions, strategies)
            conflicts.extend(subconflicts)  # FIXME XXX: Wrap or not?
            #conflicts.extend(wrap_subconflicts(key, subconflicts))
        else:
            assert nbdime.log.error("Unhandled chunk conflict type %s" % (chunktype,))

    # Attempt to resolve conflicts that occured at this level
    unresolved_conflicts.extend(tryresolve_conflicts(conflicts, decisions))

    # Resolve remaining conflicts with strategy at this level if any
    if unresolved_conflicts:
        if parent_strategy == "inline-outputs":
            # affects conflicts on string at /cells/*/outputs     or /cells/*/outputs/*
            resolve_strategy_inline_outputs(path, base, unresolved_conflicts, decisions)
            unresolved_conflicts = []
        elif parent_strategy == "clear-all":
            # TODO: Collect local diffs and remote diffs from unresolved_conflicts
            local_conflict_diffs, remote_conflict_diffs = collect_unresolved_diffs(path, unresolved_conflicts)
            decisions.add_decision(path, "clear_all", local_conflict_diffs, remote_conflict_diffs, conflict=False)
            unresolved_conflicts = []
        # TODO: Is the 'remove' strategy applied to /cells/*/outputs/*?

    # Return the rest of the conflicts
    return unresolved_conflicts


def _merge_strings(base, local_diff, remote_diff,
                   path, decisions, strategies):
    """Perform a three-way merge of strings. See docstring of merge."""
    assert isinstance(base, string_types)

    # FIXME XXX Handle if local or remote diff is ParentDeleted

    # Get base path for strategy lookup
    spath = star_path(path)

    # Get strategy for this dict
    parent_strategy = strategies.get(spath)
    unresolved_conflicts = []
    #conflicts = []

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
        unresolved_conflicts.append(
            (path[:-1], [op_patch(k, local_diff)], [op_patch(k, remote_diff)])
        )

    else:
        # Merge lines as lists
        _merge_strings.recursion = True
        base = base.splitlines(True)

        try:  # FIXME XXX: Why does this throw again?
            subconflicts = _merge_lists(
                base, local_diff, remote_diff, path, decisions, strategies)
            # FIXME XXX: Do we need to adjust the conflict diffs here?
            unresolved_conflicts.extend(subconflicts)
        finally:
            _merge_strings.recursion = False

        if unresolved_conflicts:
            if parent_strategy == "inline-source":
                # affects conflicts on string at /cells/*/source      or /cells/*/source/*
                # FIXME XXX: Call this here or after trying to merge
                resolve_strategy_inline_source(path, base, unresolved_conflicts, decisions)
                unresolved_conflicts = []

    return unresolved_conflicts

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
        strategies = {}  # FIXME: Create dummy with .transients or require strategies
    path = ()
    decisions = MergeDecisionBuilder()

    unresolved_conflicts = _merge(base,
        local_diff, remote_diff,
        path, decisions, strategies)

    # Apply remaining conflicts (ignoring strategy, already attempted)
    # TODO: Pop unneccesary patches here?
    for (path, ld, rd, strategy) in unresolved_conflicts:
        decisions.conflict(path, ld, rd)

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
