# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from .generic import diff
from .notebooks import diff_notebooks

__all__ = ["diff", "diff_notebooks"]
