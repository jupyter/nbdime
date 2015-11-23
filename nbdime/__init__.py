# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .diffing import shallow_diff, deep_diff
from .patching import patch
from .merging import merge

__all__ = ["shallow_diff", "deep_diff", "patch", "merge"]

from ._version import __version__
