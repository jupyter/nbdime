# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.



from collections import defaultdict
from itertools import chain

import nbformat

import nbdime.log
from .chunks import chunk_typename
from .decisions import MergeDecisionBuilder, push_patch_decision
from ..diff_format import (
    DiffOp, ParentDeleted,
    op_patch, op_addrange, op_removerange, op_add, op_replace)
from ..patching import patch
from ..prettyprint import merge_render
from ..utils import join_path, resolve_path


# =============================================================================
#
# Utility code follows
#
# =============================================================================

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
                p.diff = combine_patches(p.diff + d.diff)
        else:
            newdiffs.append(d)
    return sorted(newdiffs, key=lambda x: x.key)


def adjust_patch_level(target_path, common_path, diff):
    n = len(target_path)
    assert common_path[:n] == target_path
    if n == len(target_path):
        return diff
    remainder_path = tuple(reversed(common_path[n:]))
    newdiff = []
    for d in diff:
        nd = d
        assert nd is not None
        for key in remainder_path:
            nd = op_patch(key, nd)
        newdiff.append(nd)
    return newdiff



def collect_diffs(path, decisions):
    local_diff = []
    remote_diff = []
    for d in decisions:
        ld = adjust_patch_level(path, d.common_path, d.local_diff)
        rd = adjust_patch_level(path, d.common_path, d.remote_diff)
        local_diff.extend(ld)
        remote_diff.extend(rd)
    local_diff = combine_patches(local_diff)
    remote_diff = combine_patches(remote_diff)
    return local_diff, remote_diff


def collect_conflicting_diffs(path, decisions):
    local_conflict_diffs = []
    remote_conflict_diffs = []
    for d in decisions:
        if d.conflict:
            ld = adjust_patch_level(path, d.common_path, d.local_diff)
            rd = adjust_patch_level(path, d.common_path, d.remote_diff)
            local_conflict_diffs.extend(ld)
            remote_conflict_diffs.extend(rd)
    return local_conflict_diffs, remote_conflict_diffs


def collect_unresolved_diffs(base_path, unresolved_conflicts):
    """Collect local and remote diffs from conflict tuples.

    Assumed to be on the same path."""

    # Collect diffs
    local_conflict_diffs = []
    remote_conflict_diffs = []
    for conf in unresolved_conflicts:
        (path, ld, rd, strategy) = conf

        assert base_path == path
        #assert base_path == path[:len(base_path)]
        #relative_path = path[len(base_path):]
        #assert not relative_path

        assert isinstance(ld, list)
        assert isinstance(rd, list)

        for d in ld:
            local_conflict_diffs.append(d)
        for d in rd:
            remote_conflict_diffs.append(d)

    # Combine patches into canonical tree again
    local_conflict_diffs = combine_patches(local_conflict_diffs)
    remote_conflict_diffs = combine_patches(remote_conflict_diffs)
    return local_conflict_diffs, remote_conflict_diffs



def bundle_decisions_by_index(base_path, decisions):
    """"""
    decisions_by_index = defaultdict(list)
    level = len(base_path)
    for d in decisions:
        assert base_path == d.common_path[:level], (
            'decision has incorrect base path: %r vs %r' % (d.common_path, base_path))
        if len(d.common_path) > level:
            # At least patch/patch will have common_path on a particular item
            key = d.common_path[level]
            # Wrap decision diffs in patches so common_path points to list
            prefix = d.common_path[level:]
            d = push_patch_decision(d, prefix)
        else:
            # Removerange or addrange will have common_path
            # on list and key only in the diff entries
            keys = set(e.key for e in chain(d.local_diff, d.remote_diff, d.get("custom_diff", ())))
            assert len(keys) == 1
            key, = keys
        decisions_by_index[key].append(d)
    return decisions_by_index



# =============================================================================
#
# Autoresolve code follows
#
# =============================================================================

# Thinking through conflict resolution:
# - when conflict first encountered, it's registered as dec.conflict(path, ..., strategy)
# - strategy is used in tryresolve and eventually dropped if a conflict is registered
# - when recursing and subdecisions are returned, they're added to decisions at this level
# - i.e. decisions at this point contains all conflicts not resolved for subdocument,
#   as well as unresolved conflicts for this level
# - if we have a strategy at this level, we can try to resolve all
#   conflicts of subdocument as well as those at this level

def resolve_strategy_inline_attachments(base_path, attachments, decisions):
    strategy = "inline-attachments"

    local_conflict_diffs, remote_conflict_diffs = collect_conflicting_diffs(base_path, decisions)

    # Drop conflict decisions
    decisions.decisions = [d for d in decisions if not d.conflict]

    # FIXME: Review this code.

    ldiffs_by_key = {d.key: d for d in local_conflict_diffs}
    rdiffs_by_key = {d.key: d for d in remote_conflict_diffs}
    conflict_keys = sorted(set(ldiffs_by_key) | set(rdiffs_by_key))

    for key in conflict_keys:
        # key is the attachment filename
        ld = ldiffs_by_key[key]
        rd = rdiffs_by_key[key]

        if ld.op == DiffOp.REMOVE:
            # If one side is removing and we have a conflict,
            # the other side did an edit and we keep that
            # but flag a conflict (TODO: Or don't flag conflict?)
            assert rd.op != DiffOp.REMOVE
            decisions.remote(base_path, ld, rd, conflict=True, strategy=strategy)
        elif rd.op == DiffOp.REMOVE:
            decisions.local(base_path, ld, rd, conflict=True, strategy=strategy)
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
                nbdime.log.warning(
                    "Replacing previous conflicted attachment with filename %r", local_name)
                custom_diff += [op_replace(local_name, local)]
            else:
                custom_diff += [op_add(local_name, local)]

            if remote_name in attachments:
                nbdime.log.warning(
                    "Replacing previous conflicted attachment with filename %r", remote_name)
                custom_diff += [op_replace(remote_name, remote)]
            else:
                custom_diff += [op_add(remote_name, remote)]

            decisions.custom(base_path, ld, rd, custom_diff, conflict=True, strategy=strategy)


def output_marker(text):
    return nbformat.v4.new_output("stream", name="stderr", text=text)


def _cell_marker_format(text):
    return '<span style="color:red"><b>{0}</b></span>'.format(text)


def cell_marker(text):
    return nbformat.v4.new_markdown_cell(source=_cell_marker_format(text))


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
    local_title = "local"
    remote_title = "remote"
    marker_size = 7  # default in git
    m0 = "<"*marker_size
    m1 = "="*marker_size
    m2 = ">"*marker_size

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
        outputs.append(output_marker("%s\n" % (m1,)))
        outputs.extend(routputs)
        outputs.append(output_marker("%s %s%s\n" % (m2, remote_title, rnote)))

    # Keep base output if untouched (only inserts)
    keep_base = not (lremoves or rremoves or lpatches or rpatches)
    if lremoves and rremoves:
        # Don't add anything
        pass
    elif not keep_base:
        assert not (lremoves and lpatches)
        assert not (rremoves and rpatches)
        lnote = ""
        rnote = ""

        # Insert changed output with surrounding markers
        loutputs, lnote = get_outputs_and_note(base_output, lremoves, lpatches)
        routputs, rnote = get_outputs_and_note(base_output, rremoves, rpatches)

        outputs.append(output_marker("%s %s%s\n" % (m0, local_title, lnote)))
        outputs.extend(loutputs)
        outputs.append(output_marker("%s\n" % (m1,)))
        outputs.extend(routputs)
        outputs.append(output_marker("%s %s%s\n" % (m2, remote_title, rnote)))

    # Return marked up output
    return outputs, keep_base



def make_inline_cell_conflict(base_cells, local_diff, remote_diff):
    """Make a list of outputs with conflict markers from conflicting
    local and remote diffs.

    base_cells should be the entire cells array of the base notebook.
    """
    # Note: This is currently only used for conflicting, *non-similar*
    # insertions/replacements.
    assert 1 <= len(local_diff) <= 2
    assert 1 <= len(remote_diff) <= 2
    assert local_diff[0].op == DiffOp.ADDRANGE and remote_diff[0].op == DiffOp.ADDRANGE
    assert len(local_diff) == 1 or local_diff[1].op == DiffOp.REMOVERANGE
    assert len(remote_diff) == 1 or remote_diff[1].op == DiffOp.REMOVERANGE

    # Styling details
    local_title = "local"
    remote_title = "remote"
    marker_size = 7  # default in git
    m0 = "<"*marker_size
    m1 = "="*marker_size
    m2 = ">"*marker_size

    lremove = local_diff[1].length if len(local_diff) > 1 else 0
    rremove = remote_diff[1].length if len(remote_diff) > 1 else 0

    start = local_diff[0].key
    lkeep = max(0, lremove - rremove)
    rkeep = max(0, rremove - lremove)

    lcells = local_diff[0].valuelist + base_cells[start : start + lkeep]
    rcells = remote_diff[0].valuelist + base_cells[start : start + rkeep]

    cells = []
    cells.append(cell_marker("%s %s" % (m0, local_title)))
    cells.extend(lcells)
    cells.append(cell_marker("%s" % (m1,)))
    cells.extend(rcells)
    cells.append(cell_marker("%s %s" % (m2, remote_title)))

    # Return marked up cells
    return cells


def resolve_strategy_remove_outputs(base_path, outputs, decisions):
    strategy = "remove"

    decisions_by_index = bundle_decisions_by_index(base_path, decisions)
    decisions.decisions = []
    for key, decs in sorted(decisions_by_index.items()):
        if not any(d.conflict for d in decs):
            decisions.decisions.extend(decs)
        else:
            # Replace all decisions affecting key with resolution
            local_diff, remote_diff = collect_diffs(base_path, decs)
            if (
                len(local_diff) == len(remote_diff) == 1 and
                local_diff[0].op == remote_diff[0].op == DiffOp.ADDRANGE
            ):
                # remove in add vs add is a no-op
                custom_diff = []
            else:
                custom_diff = [op_removerange(key, 1)]
            decisions.custom(base_path, local_diff, remote_diff,
                custom_diff, conflict=False, strategy=strategy)


def resolve_strategy_inline_outputs(base_path, outputs, decisions):
    strategy = "inline-outputs"

    decisions_by_index = bundle_decisions_by_index(base_path, decisions)
    decisions.decisions = []
    for key, decs in sorted(decisions_by_index.items()):
        if not any(d.conflict for d in decs):
            decisions.decisions.extend(decs)
        else:
            # Replace all decisions affecting key with resolution
            local_diff, remote_diff = collect_diffs(base_path, decs)
            inlined_conflict, keep_base = make_inline_output_conflict(
                outputs[key] if outputs else None, local_diff, remote_diff)
            custom_diff = []
            custom_diff += [op_addrange(key, inlined_conflict)]
            if not keep_base:
                custom_diff += [op_removerange(key, 1)]
            decisions.custom(base_path, local_diff, remote_diff, custom_diff, conflict=True, strategy=strategy)


def resolve_strategy_record_conflicts(base_path, base, decisions):
    strategy = "record-conflict"

    decisions.decisions = [push_patch_decision(d, d.common_path[len(base_path):]) for d in decisions]

    local_conflict_diffs, remote_conflict_diffs = collect_conflicting_diffs(base_path, decisions)
    #local_diff, remote_diff = collect_diffs(base_path, decisions)

    local_conflict_diffs = combine_patches(local_conflict_diffs)
    remote_conflict_diffs = combine_patches(remote_conflict_diffs)

    # Drop conflict decisions
    #conflict_decisions = [d for d in decisions if d.conflict]
    decisions.decisions = [d for d in decisions if not d.conflict]

    # Record remaining conflicts in field nbdime-conflicts
    conflicts_dict = {
        "local_diff": local_conflict_diffs,
        "remote_diff": remote_conflict_diffs,
        # TODO: Record local and remote versions of full metadata, easier to manually select one?
        #"base_metadata": base,
        #"local_metadata": patch(base, local_diff),
        #"remote_metadata": patch(base, remote_diff),
    }
    if "nbdime-conflicts" in base:
        nbdime.log.warning("Replacing previous nbdime-conflicts field from base notebook.")
        op = op_replace("nbdime-conflicts", conflicts_dict)
    else:
        nbdime.log.warning(
            "Recording unresolved conflicts in %s/nbdime-conflicts.", join_path(base_path))
        op = op_add("nbdime-conflicts", conflicts_dict)
    custom_diff = [op]

    decisions.custom(
        base_path, local_conflict_diffs, remote_conflict_diffs, custom_diff,
        conflict=True, strategy=strategy)


def resolve_strategy_inline_source(path, base, local_diff, remote_diff):
    strategy = "inline-source"

    decisions = MergeDecisionBuilder()

    if local_diff is ParentDeleted:
        # Add marker at top of cell, easier to clean up manually
        local_diff = [op_addrange(0, ["<<<<<<< LOCAL CELL DELETED >>>>>>>\n"])]
        decisions.local_then_remote(path, local_diff, remote_diff, conflict=True, strategy=strategy)
    elif remote_diff is ParentDeleted:
        # Add marker at top of cell, easier to clean up manually
        remote_diff = [op_addrange(0, ["<<<<<<< REMOTE CELL DELETED >>>>>>>\n"])]
        decisions.remote_then_local(path, local_diff, remote_diff, conflict=True, strategy=strategy)
    else:
        # This is another approach, replacing content with markers
        # if local_diff is ParentDeleted:
        #     local = "<CELL DELETED>"
        # else:
        #     local = patch(base, local_diff)
        # if remote_diff is ParentDeleted:
        #     remote = "<CELL DELETED>"
        # else:
        #     remote = patch(base, remote_diff)

        # Run merge renderer on full sources
        local = patch(base, local_diff)
        remote = patch(base, remote_diff)
        merged, status = merge_render(base, local, remote, None)
        conflict = status != 0

        assert path[-1] == "source"
        custom_diff = [op_replace(path[-1], merged)]
        decisions.custom(path[:-1],
            [op_patch(path[-1], local_diff)],
            [op_patch(path[-1], remote_diff)],
            custom_diff, conflict=conflict, strategy=strategy)

    return decisions


def resolve_strategy_inline_recurse(path, base, decisions):
    strategy = "inline-cells"

    old_decisions = decisions.decisions
    decisions.decisions = []

    for d in old_decisions:
        if not d.conflict:
            decisions.decisions.append(d)
            continue
        assert d.local_diff and d.remote_diff
        laname, lpname = chunk_typename(d.local_diff)
        raname, rpname = chunk_typename(d.remote_diff)
        chunktype = laname + lpname + "/" + raname + rpname
        if (chunktype not in ('AR/A', 'A/AR', 'A/A', 'AR/AR') or 
                d.common_path != ('cells',)):
            decisions.decisions.append(d)
            continue
        if d.get('similar_insert', None) is None:
            # Inserts not similar, cannot recurse. Markup block
            cells = make_inline_cell_conflict(base, d.local_diff, d.remote_diff)
            rdiff = []
            if len(d.local_diff) > 1:
                rdiff.append(d.local_diff[1])
            elif len(d.remote_diff) > 1:
                rdiff.append(d.remote_diff[1])

            decisions.custom(path,
                d.local_diff,
                d.remote_diff,
                [op_addrange(d.local_diff[0].key, cells)] + rdiff,
                conflict=True,
                strategy=strategy)
            continue
        # Should only be insert range vs insertion range here now:
        # FIXME: Remove asserts when sure there are no missed corner cases:
        assert chunktype == 'A/A', 'Unexpected chunk type: %r' % chunktype

        # We have conflicting, similar inserts, should only be one cell per decision
        if not (len(d.local_diff[0].valuelist) == len(d.remote_diff[0].valuelist) == 1):
            raise AssertionError('Unexpected diff length. Expected both local and remote '
                                 'inserts to have length 1, as they are assumed similar.')

        custom_diff = []
        # Diff of local to remote:
        lr_diff = d.similar_insert
        assert lr_diff[0].op == 'patch'
        lcell = d.local_diff[0].valuelist[0]
        rcell = d.remote_diff[0].valuelist[0]

        assert lcell['cell_type'] == rcell['cell_type'], 'cell types cannot differ'

        cell = {}
        keys = [e.key for e in lr_diff[0].diff]

        for k in lcell.keys():
            if k not in keys:
                # either identical, or one-way from local
                cell[k] = lcell[k]
        for k in rcell.keys():
            if k not in keys and k not in lcell:
                # one-way from remote
                cell[k] = rcell[k]

        for k in keys:
            if k == 'source':
                cell[k] = merge_render('', lcell[k], rcell[k], None)[0]

            elif k == 'metadata':
                cell[k] = {
                    "local_metadata": lcell[k],
                    "remote_metadata": rcell[k],
                }

            elif k == 'id':
                cell[k] = {
                    "local_id": lcell[k],
                    "remote_id": rcell[k],
                }

            elif k == 'execution_count':
                cell[k] = None  # Clear

            elif k == 'outputs':
                cell[k] = []
                # TODO: Do inline merge
                pass

            else:
                raise ValueError('Conflict on unrecognized key: %r' % (k,))

        custom_diff = [op_addrange(d.local_diff[0].key, [cell])]

        decisions.custom(path,
            d.local_diff,
            d.remote_diff,
            custom_diff,
            conflict=True,
            strategy=strategy)


def resolve_strategy_generic(path, decisions, strategy):
    if not (strategy and strategy != "mergetool" and decisions.has_conflicted()):
        return

    if strategy.startswith("use-"):
        # Example: /cells strategy use-local,
        # patch/remove conflict on /cells/3,
        # decision is changed to action=local
        action = strategy.replace("use-", "")
        for d in decisions:
            # Resolve conflicts that aren't marked with an
            # already applied strategy. This applies to
            # at least the inline conflict strategies.
            if d.conflict and not d.get("strategy"):
                d.action = action
                d.conflict = False
    else:
        msg = "Unexpected strategy {} on {}.".format(
            strategy, join_path(path))
        nbdime.log.error(msg)


def resolve_conflicted_decisions_list(path, base, decisions, strategy):
    if not (strategy and strategy != "mergetool" and decisions.has_conflicted()):
        return

    if strategy == "inline-outputs":
        # Affects conflicts on output dicts at /cells/*/outputs
        resolve_strategy_inline_outputs(path, base, decisions)

    elif strategy == "inline-cells":
        # Affects conflicts on cell dicts at /cells/*
        resolve_strategy_inline_recurse(path, base, decisions)

    elif strategy == "remove":
        # Affects conflicts on output dicts at /cells/*/outputs
        resolve_strategy_remove_outputs(path, base, decisions)

    elif strategy == "union":
        action = "local_then_remote"
        for d in decisions:
            if d.conflict:
                # do not to apply to subdecisions on dicts
                if not isinstance(resolve_path(base, d.common_path[len(path):]), dict):
                    d.action = action
                    d.conflict = False

    elif strategy == "clear-all":
        # Old approach that relies on special handling in apply_decisions
        # to deal with clear-all overriding other decisions:
        # Collect local diffs and remote diffs from unresolved_conflicts
        #local_conflict_diffs, remote_conflict_diffs = collect_conflicting_diffs(path, decisions)
        #decisions.add_decision(path, "clear_all", local_conflict_diffs, remote_conflict_diffs, conflict=False)

        # Just drop all decisions and add a decision to remove the entire range
        local_diff, remote_diff = collect_diffs(path, decisions)
        custom_diff = [op_removerange(0, len(base))]
        decisions.decisions = []
        decisions.custom(path, local_diff, remote_diff, custom_diff, conflict=False, strategy=strategy)

    elif strategy == "clear":
        # FIXME: Only getting here when base is a list of the lines in a string,
        # actually resolved in resolve_conflicted_decisions_strings
        # Avoid error message in generic
        pass

    else:
        resolve_strategy_generic(path, decisions, strategy)


def resolve_conflicted_decisions_dict(path, base, decisions, strategy):
    if not (strategy and strategy != "mergetool" and decisions.has_conflicted()):
        return

    if strategy == "record-conflict":
        # affects conflicts on dicts at /***/metadata or below
        resolve_strategy_record_conflicts(path, base, decisions)

    elif strategy == "inline-attachments":
        # affects conflicts on string at /cells/*/attachments or below
        resolve_strategy_inline_attachments(path, base, decisions)

    elif strategy == "union":
        # union ops on dicts doesn't really work if they are decided to be conflicting
        for d in decisions:
            if d.conflict:
                msg = "Unexpected strategy {} for dict on {}.".format(
                    strategy, join_path(path))
                nbdime.log.error(msg)

    else:
        resolve_strategy_generic(path, decisions, strategy)


def resolve_conflicted_decisions_strings(path, decisions, strategy):
    if not (strategy and strategy != "mergetool" and decisions.has_conflicted()):
        return

    if strategy == "clear":
        for d in decisions:
            if d.conflict and not d.get("strategy"):
                d.action = "clear"
                d.conflict = False
    elif strategy == "inline-source":
        # Avoid error message in generic
        pass
    else:
        resolve_strategy_generic(path, decisions, strategy)
