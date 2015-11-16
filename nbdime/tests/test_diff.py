#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from nbdime import diff, patch
from nbdime.diff.validation import is_valid_diff

def test_generic_diff():
    a = []
    b = []
    d = diff(a, b)
    assert is_valid_diff(d)
    assert patch(a, d) == b
