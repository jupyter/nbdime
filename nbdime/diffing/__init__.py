# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .deep import deep_diff
from .shallow import shallow_diff
from .notebooks import diff_notebooks

__all__ = ["shallow_diff", "deep_diff", "diff_notebooks"]
