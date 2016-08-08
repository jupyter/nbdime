# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from .decisions import decide_merge, apply_decisions
from .notebooks import merge_notebooks

__all__ = ["decide_merge", "merge_notebooks"]
