# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .diffing import shallow_diff, deep_diff, diff_notebooks
from .patching import patch, patch_notebook
from .merging import merge

__all__ = ["shallow_diff", "deep_diff", "diff_notebooks", "patch", "patch_notebook", "merge"]

from ._version import __version__
