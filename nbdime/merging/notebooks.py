# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

#from six import string_types
#from six.moves import xrange as range

import nbformat

#from ..diffing import diff
#from ..dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE
from .generic import merge


def merge_notebooks(base, local, remote):
    """Merge changes introduced by notebooks local and remote from a shared ancestor base.

    Return new (partially) merged notebook and unapplied diffs from the local and remote side.
    """
    # FIXME: Implement notebook aware merge
    merged, local_conflict_diffs, remote_conflict_diffs = merge(base, local, remote)
    return nbformat.from_dict(merged), local_conflict_diffs, remote_conflict_diffs
