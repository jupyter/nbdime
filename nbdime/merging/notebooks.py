# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from .decisions import merge_with_diff, apply_decisions, split_path
from .autoresolve_decisions import autoresolve_decisions
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


class Strategies(dict):
    """Simple dict wrapper for strategies to allow for wildcard matching of
    list indices.
    """
    def __init__(self, *args, **kwargs):
        self.transients = kwargs.get("transients", [])
        super(Strategies, self).__init__(*args, **kwargs)

    def get(self, k, d=None):
        parts = split_path(k)
        if len(parts) > 1:
            for i, p in enumerate(parts):
                if p.isnumeric():
                    parts[i] = '*'
            key = "/" + "/".join(parts)
        else:
            key = k
        return super(Strategies, self).get(key, d)


def autoresolve_notebook_conflicts(base, decisions, args):
    strategies = Strategies({
        "/nbformat": "fail",
        "/nbformat_minor": "fail",
        "/cells/*/execution_count": "clear",
        "/cells/*/cell_type": "fail",
        },
        transients=[
            "/cells/*/execution_count",
            "/cells/*/outputs",
            "/cells/*/metadata/collapsed",
            "/cells/*/metadata/autoscroll",
            "/cells/*/outputs/*/execution_count"
        ])
    if args and args.strategy == "mergetool":
        strategies.update({
            "/cells/*/source": "mergetool",
            "/cells/*/outputs": "mergetool",
            "/cells/*/outputs/*/execution_count": "clear",
        })
    else:
        strategies.update({
            "/metadata": "record-conflict",
            "/cells/*/metadata": "record-conflict",
            "/cells/*/source": "mergetool",
            "/cells/*/source": "inline-source",
            "/cells/*/outputs": "inline-outputs", # "clear", "join"
            # FIXME: Find a good way to handle strategies for both parent (outputs) and child (execution_count).
            #        It might be that some strategies can be combined while others don't make sense, e.g. setting use-* on parent.
            #"/cells/*/outputs/*/execution_count": "clear",
            #"/cells/*/outputs/*/metadata": "record-conflict",
        })
    return autoresolve_decisions(base, decisions, strategies)


def decide_notebook_merge(base, local, remote, args=None):
    # Compute notebook specific diffs
    local_diffs = diff_notebooks(base, local)
    remote_diffs = diff_notebooks(base, remote)

    # Execute a generic merge operation
    decisions = merge_with_diff(base, local, remote, local_diffs, remote_diffs)

    # Try to resolve conflicts based on behavioural options
    decisions = autoresolve_notebook_conflicts(base, decisions, args)

    return decisions


def merge_notebooks(base, local, remote, args=None):
    """Merge changes introduced by notebooks local and remote from a shared ancestor base.

    Return new (partially) merged notebook and unapplied diffs from the local and remote side.
    """
    decisions = decide_notebook_merge(base, local, remote, args)
    return apply_decisions(base, decisions), decisions
