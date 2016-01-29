# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import nbformat

from .generic import merge

def merge_notebooks(base, local, remote):
    """Merge changes introduced by notebooks local and remote from a shared ancestor base.

    Return new (partially) merged notebook and unapplied diffs from the local and remote side.
    """
    merged, local_conflict_diffs, remote_conflict_diffs = merge(base, local, remote)
    merged = nbformat.from_dict(merged)
    return merged, local_conflict_diffs, remote_conflict_diffs
