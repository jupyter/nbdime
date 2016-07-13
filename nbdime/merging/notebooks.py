# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import nbformat

from .generic import merge_with_diff
from .autoresolve import autoresolve
from ..patching import patch
from ..diffing.notebooks import diff_notebooks


# Strategies for handling conflicts  TODO: Implement these and refine further!
generic_conflict_strategies = ("mergetool", "fail", "use-base", "use-local", "use-remote", "clear")
source_conflict_strategies = generic_conflict_strategies # + ("inline-source",)
transient_conflict_strategies = generic_conflict_strategies # + ()
output_conflict_strategies = transient_conflict_strategies # + ("join", "inline-outputs")


def autoresolve_notebook_conflicts(merged, local_diffs, remote_diffs, args):
    strategies = {
        "/nbformat": "fail",
        "/nbformat_minor": "fail",
        "/metadata": "use-base",
        "/cells/*/cell_type": "fail",
        "/cells/*/execution_count": "clear",
        "/cells/*/metadata": "use-base",
        #"/cells/*/source": "inline-source",  # FIXME: Debug this mode
        "/cells/*/source": "mergetool",
        "/cells/*/outputs": "inline-outputs", # "clear", "join"
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
