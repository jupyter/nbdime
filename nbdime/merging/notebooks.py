# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import logging
from six import StringIO

from .generic import decide_merge_with_diff
from .decisions import apply_decisions
from .autoresolve import autoresolve
from ..diffing.notebooks import diff_notebooks
from ..utils import Strategies
from ..prettyprint import pretty_print_notebook_diff, pretty_print_merge_decisions, pretty_print_notebook


_logger = logging.getLogger(__name__)


# Strategies for handling conflicts  TODO: Implement these and refine further!
generic_conflict_strategies = (
    "fail",             # Unexpected: crash and burn in case of conflict
    "mergetool",        # Do not modify decision (but prevent processing at deeper path)
    "use-base",         # Keep base value in case of conflict
    "use-local",        # Use local value in case of conflict
    "use-remote",       # Use remote value in case of conflict
    "clear",            # Discard value in case of conflict
    "record-conflict",  # Valid for metadata only: produce new metadata with conflicts recorded for external inspection
    "inline-source",    # Valid for source only: produce new source with inline diff markers
    "inline-outputs",   # Valid for outputs only: produce new outputs with inline diff markers
    "join",             # Join values in case of conflict, don't insert new markers.
    )

# Strategies that can be applied to an entire notebook
cli_conflict_strategies = (
    "use-base",         # Keep base value in case of conflict
    "use-local",        # Use local value in case of conflict
    "use-remote",       # Use remote value in case of conflict
    "union",            # Take local value, then remote, in case of conflict
    "inline",           # Inline source and outputs, and record metadata conflicts
)


def autoresolve_notebook_conflicts(base, decisions, args):
    strategies = Strategies({
        "/nbformat": "fail",
        # "/nbformat_minor": "fail",
        "/cells/*/cell_type": "fail",
        })

    if not args or args.ignore_transients:
        strategies.transients = [
            "/cells/*/execution_count",
            "/cells/*/outputs",
            "/cells/*/metadata/collapsed",
            "/cells/*/metadata/autoscroll",
            "/cells/*/metadata/scrolled",
            "/cells/*/outputs/*/execution_count"
        ]
        strategies.update({
            "/cells/*/execution_count": "clear",
            "/cells/*/outputs/*/execution_count": "clear",
        })
    merge_strategy = args.merge_strategy if args else "inline"
    input_strategy = args.input_strategy if args else None
    output_strategy = args.output_strategy if args else None
    if merge_strategy == "mergetool":
        # Mergetool strategy will prevent autoresolve from
        # attempting to solve conflicts on these entries:
        strategies.update({
            "/cells/*/source": "mergetool",
            "/cells/*/outputs": "mergetool",
            "/cells/*/attachments": "mergetool",
        })
    elif merge_strategy.startswith('use-'):
        strategies.fall_back = args.merge_strategy
    else:
        strategies.update({
            "/metadata": "record-conflict",
            "/cells/*/metadata": "record-conflict",
            "/cells/*/source": "inline-source",
            "/cells/*/outputs": "inline-outputs",
            # TODO: Add an inline strategy for attachments as well
            # FIXME: Find a good way to handle strategies for both parent (outputs) and child (execution_count).
            #        It might be that some strategies can be combined while others don't make sense, e.g. setting use-* on parent.
        })
    if input_strategy:
        strategies.update({
            "/cells/*/source": input_strategy
        })
    if output_strategy:
        strategies.update({
            "/cells/*/outputs": output_strategy
        })
    return autoresolve(base, decisions, strategies)


def decide_notebook_merge(base, local, remote, args=None):
    # Compute notebook specific diffs
    local_diffs = diff_notebooks(base, local)
    remote_diffs = diff_notebooks(base, remote)

    if args and args.log_level == "DEBUG":
        _logger.debug("In merge, base-local diff:")
        buf = StringIO()
        pretty_print_notebook_diff("<base>", "<local>", base, local_diffs, buf)
        _logger.debug(buf.getvalue())

        _logger.debug("In merge, base-remote diff:")
        buf = StringIO()
        pretty_print_notebook_diff("<base>", "<remote>", base, remote_diffs, buf)
        _logger.debug(buf.getvalue())

    # Execute a generic merge operation
    decisions = decide_merge_with_diff(
        base, local, remote, local_diffs, remote_diffs)

    if args and args.log_level == "DEBUG":
        _logger.debug("In merge, initial decisions:")
        buf = StringIO()
        pretty_print_merge_decisions(base, decisions, buf)
        _logger.debug(buf.getvalue())

    # Try to resolve conflicts based on behavioural options
    decisions = autoresolve_notebook_conflicts(base, decisions, args)

    if args and args.log_level == "DEBUG":
        _logger.debug("In merge, autoresolved decisions:")
        buf = StringIO()
        pretty_print_merge_decisions(base, decisions, buf)
        _logger.debug(buf.getvalue())

    return decisions


def merge_notebooks(base, local, remote, args=None):
    """Merge changes introduced by notebooks local and remote from a shared ancestor base.

    Return new (partially) merged notebook and unapplied diffs from the local and remote side.
    """
    if args and args.log_level == "DEBUG":
        for (name, nb) in [("base", base), ("local", local), ("remote", remote)]:
            _logger.debug("%s In merge, input %s notebook:" % ("="*20, name))
            buf = StringIO()
            pretty_print_notebook(nb, None, buf)
            _logger.debug(buf.getvalue())

    decisions = decide_notebook_merge(base, local, remote, args)

    merged = apply_decisions(base, decisions)

    if args and args.log_level == "DEBUG":
        _logger.debug("%s In merge, merged notebook:" % ("="*20,))
        buf = StringIO()
        pretty_print_notebook(merged, None, buf)
        _logger.debug(buf.getvalue())
        _logger.debug("%s End merge" % ("="*20,))

    return merged, decisions
