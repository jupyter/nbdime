# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function, unicode_literals

from six import string_types
import copy
import logging
from itertools import chain

import nbformat
from nbformat import NotebookNode

from ..diff_format import DiffOp, DiffEntry, Deleted, op_replace, op_removerange, op_addrange, op_patch, op_add, op_remove
from ..patching import patch, patch_singleline_string
from .chunks import make_merge_chunks
from ..utils import join_path, split_path, star_path, is_prefix_array, resolve_path
from .decisions import (pop_patch_decision, push_patch_decision, MergeDecision,
                        pop_all_patch_decisions, _sort_key,
                        filter_decisions, build_diffs)
from ..prettyprint import merge_render
from .generic import is_diff_all_transients

import nbdime.log


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


def split_decisions_by_cell(decisions):
    generic_decisions = []
    cell_decisions = []
    for dec in decisions:
        if dec.common_path[:1] != ("cells",):
            generic_decisions.append(dec)
        else:
            cell_decisions.append(dec)

    return generic_decisions, cell_decisions


def make_bundled_decisions(base, prefix, decisions, callback):
    """Bundle a collection of decisions on a prefix

    All decisions must have the same (unstarred) path prefix.
    """
    if not any(dec.conflict for dec in decisions):
        # no conflicts, nothing to do
        [dec.pop('_level') for dec in decisions]
        return decisions

    resolved_base = resolve_path(base, prefix)
    local_diff = build_diffs(resolved_base, decisions, 'local')
    remote_diff = build_diffs(resolved_base, decisions, 'remote')

    return callback(resolved_base, prefix, local_diff, remote_diff)


def bundle_decisions(base, decisions, pattern, callback):
    indices = filter_decisions(pattern, decisions)
    index_set = set(indices)
    # all the decisions I'm not bundling:
    other_decisions = [decisions[i] for i in range(len(decisions)) if i not in index_set]

    # group decisions on any given source
    decision_groups = {}
    for i in indices:
        dec = decisions[i]
        level = len(split_path(pattern))
        prefix = dec.common_path[:level]
        if prefix not in decision_groups:
            decision_groups[prefix] = []
        dec._level = level
        decision_groups[prefix].append(dec)

    # create bundles for each unique prefix
    affected_decisions = []
    for prefix, dec_group in decision_groups.items():
        bundled_decisions = make_bundled_decisions(base, prefix, dec_group, callback)
        affected_decisions.extend(bundled_decisions)

    return other_decisions + affected_decisions
