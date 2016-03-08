# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import nbformat

from .generic import merge
from ..diff_format import as_dict_based_diff


# Strategies for handling conflicts  TODO: Implement these and refine further!
generic_conflict_strategies = ("mergetool", "use-base", "use-local", "use-remote")
source_conflict_strategies = generic_conflict_strategies + ("add-markers",)
transient_conflict_strategies = generic_conflict_strategies + ("invalidate",)
output_conflict_strategies = transient_conflict_strategies + ("use-all",)


def autoresolve_notebook_conflicts(merged, local_conflict_diffs, remote_conflict_diffs, args):
    assert isinstance(merged, dict)

    # Converting to dict-based diff format for dicts for convenience
    # This step will be unnecessary if we change the diff format to work this way always
    lcd = as_dict_based_diff(local_conflict_diffs)
    rcd = as_dict_based_diff(remote_conflict_diffs)
    # FIXME: Step through nbformat docs and handle case by case


    strategy = args.strategy
    if strategy not in generic_conflict_strategies:
        raise ValueError("Invalid strategy {}".format(strategy))

    # TODO: We want to be a lot more sophisticated than this, e.g.
    #   setting different strategies for source, output, metadata etc.
    #   However this is illustrative and was quick and easy to implement.

    if strategy == "mergetool":
        pass
    elif strategy == "use-base":
        local_conflict_diffs = []
        remote_conflict_diffs = []
    elif strategy == "use-local":
        merged = patch(merged, local_conflict_diffs)
        local_conflict_diffs = []
        remote_conflict_diffs = []
    elif strategy == "use-remote":
        merged = patch(merged, remote_conflict_diffs)
        local_conflict_diffs = []
        remote_conflict_diffs = []

    return merged, local_conflict_diffs, remote_conflict_diffs


def merge_notebooks(base, local, remote, args):
    """Merge changes introduced by notebooks local and remote from a shared ancestor base.

    Return new (partially) merged notebook and unapplied diffs from the local and remote side.
    """
    # Execute a generic merge operation
    merged, local_conflict_diffs, remote_conflict_diffs = merge(base, local, remote)
    merged = nbformat.from_dict(merged)

    # Try to resolve conflicts based on behavioural options
    #merged, local_conflict_diffs, remote_conflict_diffs = \
    #  autoresolve_notebook_conflicts(merged, local_conflict_diffs, remote_conflict_diffs, args)

    return merged, local_conflict_diffs, remote_conflict_diffs
