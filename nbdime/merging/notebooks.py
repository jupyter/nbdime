# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import nbformat

from .generic import merge_with_diff
from .autoresolve import autoresolve
#from ..patching import patch
from ..diffing.notebooks import diff_notebooks


# Strategies for handling conflicts  TODO: Implement these and refine further!
generic_conflict_strategies = (
    "fail",             # Unexpected: crash and burn in case of conflict
    "mergetool",        # Pass on diff to external difftool (TODO: store in global metadata at end instead of in separate diff dicts?)
    "use-base",         # Keep base value in case of conflict
    "use-local",        # Use local value in case of conflict
    "use-remote",       # Use remote value in case of conflict
    "clear",            # Discard value in case of conflict
    "record-conflict",  # Valid for metadata only: produce new metadata with conflicts recorded for external inspection
    "inline-source",    # Valid for source only: produce new source with inline diff markers
    "inline-outputs",   # Valid for outputs only: produce new outputs with inline diff markers
    "join",             # Join values in case of conflict, don't insert new markers.
    )


def autoresolve_notebook_conflicts(merged, local_diffs, remote_diffs, args):
    strategies = {
        "/nbformat": "fail",
        "/nbformat_minor": "fail",
        "/metadata": "record-conflict",
        "/cells/*/cell_type": "fail",
        "/cells/*/execution_count": "clear",
        "/cells/*/metadata": "record-conflict",
        "/cells/*/source": "mergetool",
        #"/cells/*/source": "inline-source",
        "/cells/*/outputs": "inline-outputs", # "clear", "join"
        # FIXME: Find a good way to handle strategies for both parent (outputs) and child (execution_count).
        #        It might be that some strategies can be combined while others don't make sense, e.g. setting use-* on parent.
        #"/cells/*/outputs/*/execution_count": "clear",
        #"/cells/*/outputs/*/metadata": "record-conflict",
        }
    resolved, local_diffs, remote_diffs = \
        autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    return resolved, local_diffs, remote_diffs


def merge_notebooks(base, local, remote, args=None):
    """Merge changes introduced by notebooks local and remote from a shared ancestor base.

    Return new (partially) merged notebook and unapplied diffs from the local and remote side.
    """
    # Compute notebook specific diffs
    local_diffs = diff_notebooks(base, local)
    remote_diffs = diff_notebooks(base, remote)

    # Execute a generic merge operation
    merged, local_diffs, remote_diffs = merge_with_diff(base, local, remote, local_diffs, remote_diffs)

    # Try to resolve conflicts based on behavioural options
    resolved, local_diffs, remote_diffs = \
      autoresolve_notebook_conflicts(merged, local_diffs, remote_diffs, args)

    resolved = nbformat.from_dict(resolved)
    return resolved, local_diffs, remote_diffs
