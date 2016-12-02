# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function, unicode_literals

from six import string_types
import copy
import logging

import nbformat
from nbformat import NotebookNode

from ..diff_format import DiffOp, DiffEntry, op_replace, op_removerange, op_addrange, op_patch
from ..patching import patch, patch_singleline_string
from .chunks import make_merge_chunks
from ..utils import join_path, star_path
from .decisions import (pop_patch_decision, push_patch_decision, MergeDecision,
                        pop_all_patch_decisions, _sort_key,
                        filter_decisions, build_diffs,
                        )
from ..prettyprint import merge_render

import nbdime.log

_logger = logging.getLogger(__name__)


def add_conflicts_record(value, le, re):
    """Add an item 'nbdime-conflicts' to a metadata dict.

    Simply storing metadata conflicts for mergetool inspection.
    """
    assert isinstance(value, dict)
    c = {}
    if le is not None:
        c["local"] = le
    if re is not None:
        c["remote"] = re
    newvalue = NotebookNode(value)
    newvalue["nbdime-conflicts"] = c
    return newvalue


# Sentinel object
Deleted = object()


def patch_item(value, diffentry):
    if diffentry is None:
        return value
    op = diffentry.op
    if op == DiffOp.REPLACE:
        return diffentry.value
    elif op == DiffOp.PATCH:
        return patch(value, diffentry.diff)
    elif op == DiffOp.REMOVE:
        return Deleted
    else:
        raise ValueError("Invalid item patch op {}".format(op))


def make_join_value(value, le, re):
    # Joining e.g. an outputs list means concatenating all items
    lvalue = patch_item(value, le)
    rvalue = patch_item(value, re)

    if lvalue is Deleted:
        lvalue = []
    if rvalue is Deleted:
        rvalue = []

    # New list
    newvalue = value + lvalue + rvalue

    return newvalue


def output_marker(text):
    return nbformat.v4.new_output("stream", name="stderr", text=text)


def make_inline_outputs_value(base, le, re,
                              base_title="base", local_title="local", remote_title="remote"):
    # Produce local/remote values; lists of outputs
    values = []
    notes = []
    for e in (le, re):
        if e == "deleted":
            note = " <CELL DELETED>"
            value = [output_marker("<CELL DELETED>")]
        else:
            # TODO: Add touched fields from diff e to note
            note = ""
            value = patch_item(base, e)
            if value is Deleted:
                value = []
        values.append(value)
        notes.append(note)
    local, remote = values
    local_note, remote_note = notes

    # Define markers
    include_base = True  # TODO: Make option
    marker_size = 7  # default in git
    sep0 = "<"*marker_size
    sep1 = "|"*marker_size
    sep2 = "="*marker_size
    sep3 = ">"*marker_size

    sep0 = "%s %s%s\n" % (sep0, local_title, local_note)
    sep1 = "%s %s\n" % (sep1, base_title)
    sep2 = "%s\n" % (sep2,)
    sep3 = "%s %s%s" % (sep3, remote_title, remote_note)

    # Note: This is very notebook specific while the rest of this file is more generic
    outputs = []
    outputs.append(output_marker(sep0))
    outputs.extend(local)
    if include_base:
        outputs.append(output_marker(sep1))
        outputs.extend(base)
    outputs.append(output_marker(sep2))
    outputs.extend(remote)
    outputs.append(output_marker(sep3))

    return outputs


def _analyse_edited_lines(baselines, patch_op):
    # Strip single patch op on "source"
    assert patch_op.op == DiffOp.PATCH
    assert patch_op.key == "source"

    diff = patch_op.diff

    assert len(diff) in (1, 2)
    if len(diff) == 2:
        assert DiffOp.ADDRANGE in [e.op for e in diff]

    lines = []
    addlines = []
    #deleted_min = len(baselines)
    #deleted_max = 0
    deleted_min = min(e.key for e in diff)
    assert all(e.key == deleted_min for e in diff)
    deleted_max = deleted_min

    for e in diff:
        if e.op == DiffOp.ADDRANGE:
            # Only add lines to base
            assert not addlines
            addlines = e.valuelist
        elif e.op == DiffOp.REMOVERANGE:
            # Only remove lines from base
            deleted_min = e.key
            deleted_max = e.key + e.length
        elif e.op == DiffOp.REPLACE:
            # Replace single line with given value
            assert not lines
            lines = [e.value]
            deleted_min = e.key
            deleted_max = e.key + 1
        elif e.op == DiffOp.PATCH:
            # Replace single line with patched value
            assert not lines
            lines = [patch_singleline_string(baselines[e.key], e.diff)]
            deleted_min = e.key
            deleted_max = e.key + 1
        else:
            raise ValueError("Invalid item patch op {}".format(e.op))

    lines = addlines + lines
    return lines, deleted_min, deleted_max


def make_inline_source_value(base, local_diff, remote_diff):
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


def strategy2action_dict(resolved_base, le, re, strategy, path, dec):
    assert le is None or re is None or le.key == re.key
    key = le.key if re is None else re.key

    nbdime.log.warning('autoresolving conflict at %s with %s' % (path, strategy))

    # Make a shallow copy of dec
    dec = copy.copy(dec)

    # The rest here remove the conflicts and provide a new value
    # ... cases ignoring changes
    if strategy == "clear":
        dec.action = "clear"
        dec.conflict = False
    elif strategy == "clear-parent":
        dec.action = "clear_parent"
        dec.conflict = False
    elif strategy == "use-base":
        dec.action = "base"
        dec.conflict = False
    # ... cases ignoring changes from one side
    elif strategy == "use-local":
        dec.action = "local"
        dec.conflict = False
    elif strategy == "use-remote":
        dec.action = "remote"
        dec.conflict = False
    elif strategy == "take-max":
        # For nbformat-minor, take max value
        bval = resolved_base[key]
        lval = le.value if le and le.op == DiffOp.REPLACE else bval
        rval = re.value if re and re.op == DiffOp.REPLACE else bval
        mval = max(bval, lval, rval)
        if bval == mval:
            return []
        elif lval == mval == rval:
            dec.action = "either"
        elif lval == mval:
            dec.action = "local"
        else:
            assert rval == mval
            dec.action = "remote"
        dec.conflict = False
    # ... cutoffs before cases using changes from both sides
    #  (NB! The position of these elif cases relative to the
    #   cases that check the strategy is important)
    elif le is None:
        # Only one sided change, use that
        dec.action = "remote"
        dec.conflict = False
    elif re is None:
        # Only one sided change, use that
        dec.action = "local"
        dec.conflict = False
    elif le == re:
        # Both changes are equal, just apply
        dec.action = "either"
        dec.conflict = False
    # ... cases using changes from both sides to produce a new value
    elif strategy == "union":
        if isinstance(resolved_base[key], (list, string_types)):
            dec.action = 'local_then_remote'
            dec.conflict = False
        else:
            # Union doesn't make sense on non-sequence types
            # Leave this conflict unresolved
            pass
    elif strategy == "inline-source":
        # inline-source is handled at a higher level
        nbdime.log.warning("inline-source should have been handled already.")
    elif strategy == "inline-attachments":
        # FIXME: Leaving this conflict unresolved until we implement a better solution
        nbdime.log.warning("Don't know how to resolve attachments yet.")
    elif strategy == "inline-outputs":
        # FIXME: Leaving this conflict unresolved until we implement a better solution
        nbdime.log.warning("Don't know how to resolve outputs yet.")
        #value = resolved_base[key]
        #newvalue = make_inline_outputs_value(value, le, re)
        #dec.custom_diff = [op_replace(key, newvalue)]
        #dec.action = "custom"
    elif strategy == "record-conflict":
        value = resolved_base[key]
        newvalue = add_conflicts_record(value, le, re)
        dec.custom_diff = [op_replace(key, newvalue)]
        dec.action = "custom"
    # ... fallthrough
    elif strategy == "mergetool":
        # Leave this type of conflict for external tool to resolve
        pass
    # ... fail
    elif strategy == "fail":
        # Expecting never to get this kind of conflict, raise error
        raise RuntimeError("Not expecting a conflict at path {}.".format(path))
    else:
        raise RuntimeError("Invalid strategy {}.".format(strategy))

    return [dec]


def strategy2action_list(strategy, dec):
    "Resolve conflicts for all items in list."

    # Make a shallow copy of dec
    dec = copy.copy(dec)

    # The rest here remove the conflicts and provide a new value
    if strategy == "use-base":
        dec.action = "base"
        dec.conflict = False
    elif strategy == "use-local":
        dec.action = "local"
        dec.conflict = False
    elif strategy == "use-remote":
        dec.action = "remote"
        dec.conflict = False
    elif strategy == "union":
        dec.action = "local_then_remote"
        dec.conflict = False
    elif strategy == "clear":
        dec.action = "clear"
        dec.conflict = False
    elif strategy == "mergetool":
        # Leave this type of conflict for external tool to resolve
        pass
    elif strategy == "clear-parent":
        dec.action = "clear_parent"
        dec.conflict = False
    elif strategy == "fail":
        raise RuntimeError("Not expecting a conflict at path {}.".format(
            join_path(dec.common_path) + '/*'))
    else:
        raise RuntimeError("Not expecting strategy {} for list items at path {}.".format(
            strategy, join_path(dec.common_path)))

    return [dec]


def autoresolve_decision_on_list(dec, base, sub, strategies):
    assert isinstance(sub, list)

    ld = dec.local_diff
    rd = dec.remote_diff

    # Query how to handle conflicts in this part of the document
    strategy = strategies.get(join_path(dec.common_path + ('*',)))

    # Cutting off handling of strategies of subitems if there's a strategy for these list items
    if strategy:
        return strategy2action_list(strategy, dec)

    # Split up and combine diffs into chunks [(begin, end, localdiffs, remotediffs)]
    chunks = make_merge_chunks(sub, ld, rd)

    # Loop over chunks of base[j:k], grouping insertion at j into
    # the chunk starting with j
    decs = []
    for (j, k, d0, d1) in chunks:
        lpatches = [e for e in d0 if e.op == DiffOp.PATCH]
        rpatches = [e for e in d1 if e.op == DiffOp.PATCH]
        i = len(decs)
        if not (d0 or d1):
            # Unmodified chunk, no-op
            pass

        elif lpatches and rpatches:
            # Recurse if we have diffs available for both subdocuments
            assert len(lpatches) == 1
            assert len(rpatches) == 1
            linserts = [e for e in d0 if e.op == DiffOp.ADDRANGE]
            rinserts = [e for e in d1 if e.op == DiffOp.ADDRANGE]
            assert len(lpatches) + len(linserts) == len(d0)
            assert len(rpatches) + len(rinserts) == len(d1)
            assert k == j + 1
            assert all(e.key == j for e in linserts + rinserts)

            subdec = copy.copy(dec)
            subdec.local_diff = lpatches
            subdec.remote_diff = rpatches
            subdec = pop_patch_decision(subdec)
            assert subdec is not None
            decs.extend(autoresolve_decision(base, subdec, strategies))

            # Patch conflicts have been processed, split off inserts if present
            # and insert before patch:
            if linserts or rinserts:
                conflict = (bool(linserts) == bool(rinserts))
                d = MergeDecision(
                    common_path=dec.common_path,
                    action="local_then_remote",  # Will this suffice?
                    conflict=conflict,
                    local_diff=linserts,  # Should these be split up further?
                    remote_diff=rinserts,
                )
                if conflict and strategies.fall_back:
                    decs.extend(strategy2action_list(
                        strategies.fall_back, d))
                else:
                    decs.insert(i, d)
        elif lpatches or rpatches:
            # One sided patch, with deletions on other (vs addition is not a
            # conflict)
            # Check that patch side only has one op (the patch)
            if lpatches:
                assert tuple(lpatches) == d0
            else:
                assert tuple(rpatches) == d1

            # Only action that can be taken is to check whether the patch ops
            # are all transients, and if so, take the other side
            for p in (lpatches or rpatches):
                # Search subpath for transients:
                subpath = dec.common_path + (p.key,)
                if not is_diff_all_transients(p.diff, subpath,
                                              strategies.transients):
                    # Cannot be auto resolved
                    subdec = copy.copy(dec)
                    subdec.local_diff = list(d0)
                    subdec.remote_diff = list(d1)
                    if strategies.fall_back:
                        # Use fall-back
                        decs.extend(strategy2action_list(
                            strategies.fall_back, subdec))
                    else:
                        decs.append(subdec)
                    break
            else:
                # All patches are all transient, pick deletion:
                subdec = copy.copy(dec)
                subdec.action = "local" if rpatches else "remote"
                subdec.conflict = False
                decs.append(subdec)

        else:
            # FIXME: What has happened here? This is hard to follow, enumerate cases!
            # - at least one side is modified
            # - only 0 or 1 has a patch
            # - one possiblity: range replacement on both sides

            # Just keep chunked decision
            subdec = copy.copy(dec)
            subdec.local_diff = list(d0)
            subdec.remote_diff = list(d1)
            # TODO: Is it always safe to use union here?
            if strategies.fall_back:
                # Use fall-back
                decs.extend(strategy2action_list(
                    strategies.fall_back, subdec))
            else:
                decs.append(subdec)

    return decs


def autoresolve_decision_on_dict(dec, base, sub, strategies):
    assert isinstance(sub, dict)

    ld = dec.local_diff
    rd = dec.remote_diff

    # I believe this to be true here
    assert len(ld) == 1 and len(rd) == 1
    assert ld[0].key == rd[0].key

    # Query how to handle conflicts in this part of the document
    key = ld[0].key
    subpath = join_path(dec.common_path + (key,))
    strategy = strategies.get(subpath)

    # Get value and conflicts
    le, = ld
    re, = rd

    if strategy is not None:
        decs = strategy2action_dict(sub, le, re, strategy, subpath, dec)
    elif le.op == DiffOp.PATCH and re.op == DiffOp.PATCH:
        assert False
        # FIXME: this is not quite right:
        # Recurse if we have no strategy for this key but diffs available for the subdocument
        newdec = pop_patch_decision(dec)
        assert newdec is not None
        decs = autoresolve_decision(base, newdec, strategies)
    elif (DiffOp.PATCH in (le.op, re.op)) and (DiffOp.REMOVE in (le.op, re.op)) and strategies.transients:
        # Check for deletion vs. purely ignoreable changes (transients)
        # If not, leave conflicted
        patchop = le if le.op == DiffOp.PATCH else re
        if is_diff_all_transients(patchop.diff, dec.common_path + (key,),
                                  strategies.transients):
            # Go with deletion, and remove conflict
            dec.action = "local" if le.op == DiffOp.REMOVE else "remote"
            dec.conflict = False
        decs = [dec]
    elif strategies.fall_back:
        # Use fall back strategy:
        decs = strategy2action_dict(sub, le, re, strategies.fall_back, subpath, dec)
    else:
        # Alternatives if we don't have PATCH/PATCH or PATCH/REMOVE, are:
        #  - ADD/ADD: only happens if inserted values are different,
        #         could possibly autoresolve some cases but nothing important
        #  - REPLACE: technically possible, if so we can can convert it to PATCH,
        #             but does it happen?
        # No resolution, keep original decision
        decs = [dec]
    return decs


def autoresolve_decision(base, dec, strategies):
    """Autoresolve a single conflicting decision in isolation.

    Returns a list of 1 or more decisions, with or without further conflicts.
    """
    assert dec.conflict

    decs = []

    # Get the non-empty base-local and base-remote diffs
    assert dec.local_diff and dec.remote_diff

    # Get object in base that common_path points to, but short-circuit if a
    # strategy is encountered while traversing common_path
    sub = base
    subpath = ()

    for key in dec.common_path:
        subpath = subpath + (key,)
        strategy = strategies.get(join_path(subpath))
        if strategy is not None:
            # Strategy found for intermediate path
            # Bring decision up to same level as strategy:
            dec = push_patch_decision(
                dec, dec.common_path[len(subpath)-1:])
            break
        sub = sub[key]

    if isinstance(sub, dict):
        decs = autoresolve_decision_on_dict(dec, base, sub, strategies)
    elif isinstance(sub, list):
        decs = autoresolve_decision_on_list(dec, base, sub, strategies)
    elif isinstance(sub, string_types):
        sub = sub.splitlines(True)
        decs = autoresolve_decision_on_list(dec, base, sub, strategies)
    else:
        raise RuntimeError("Expecting dict, list or string type, got " +
                           str(type(sub)))

    return [pop_all_patch_decisions(d) for d in decs]


def split_decisions_by_cell(decisions):
    generic_decisions = []
    cell_decisions = []
    for dec in decisions:
        if dec.common_path[:1] != ("cells",):
            generic_decisions.append(dec)
        else:
            cell_decisions.append(dec)

    return generic_decisions, cell_decisions


def make_bundled_source_decisions(base, cell_idx, source_decisions):
    """Bundle a collection of decisions on inline-source
    
    All decisions will be on the same source field.
    """
    if not any(dec.conflict for dec in source_decisions):
        # no conflicts, nothing to do
        return source_decisions

    source = base['cells'][cell_idx]['source']
    local_diff = build_diffs(source, source_decisions, 'local')
    remote_diff = build_diffs(source, source_decisions, 'remote')

    begin, end, inlined = make_inline_source_value(source, local_diff, remote_diff)
    custom_diff = [
        op_removerange(begin, end-begin),
        op_addrange(begin, inlined),
    ]
    
    return [MergeDecision(
        common_path=('cells', cell_idx, 'source'),
        action="custom",
        conflict=True,
        local_diff=local_diff,
        remote_diff=remote_diff,
        custom_diff=custom_diff,
    )]

def autoresolve_generic(base, decisions, strategies):
    newdecisions = []
    for dec in decisions:
        if dec.conflict:
            newdecisions.extend(autoresolve_decision(base, dec, strategies))
        else:
            newdecisions.append(dec)
    return newdecisions


def autoresolve_cells(base, decisions, strategies):
    return autoresolve_generic(base, decisions, strategies)


def bundle_inline_source_decisions(base, decisions):
    source_indices = filter_decisions('/cells/*/source', decisions)
    source_index_set = set(source_indices)
    # all the decisions I'm not bundling:
    other_decisions = [ decisions[i] for i in range(len(decisions)) if i not in source_index_set ]

    # group decisions on any given source
    source_decision_groups = {}
    for i in source_indices:
        dec = decisions[i]
        cell_idx = dec.common_path[1]
        if cell_idx not in source_decision_groups:
            source_decision_groups[cell_idx] = []
        dec._level = 3
        source_decision_groups[cell_idx].append(dec)

    # create bundles for each source
    source_decisions = []
    for cell_idx, dec_group in source_decision_groups.items():
        source_decisions.extend(make_bundled_source_decisions(base, cell_idx, dec_group))

    return other_decisions + source_decisions


def autoresolve(base, decisions, strategies):
    """Autoresolve a list of decisions with given strategy configuration.

    Returns a list of new decisions, with or without further conflicts.
    """
    generic_decisions, cell_decisions = split_decisions_by_cell(decisions)
    
    if strategies.get('/cells/*/source') == 'inline-source':
        cell_decisions = bundle_inline_source_decisions(base, cell_decisions)
    

    generic_decisions = autoresolve_generic(base, generic_decisions, strategies)

    cell_decisions = autoresolve_cells(base, cell_decisions, strategies)

    decisions = generic_decisions + cell_decisions
    return sorted(decisions, key=_sort_key, reverse=True)
