# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .patch import patch
from .diff import diff
from .merge import merge

__all__ = ["diff", "patch", "merge"]

from ._version import __version__
