#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from nbdime import patch
from nbdime.diff.diff_sequence import diff_sequence

def test_diff_sequence():
    a = """\
    def f(a, b):
        c = a * b
        return c

    def g(x):
        y = x**2
        return y
    """.splitlines()

    b = []
    assert patch(a, diff_sequence(a, b)) == b
    assert patch(b, diff_sequence(b, a)) == a

    for i in range(len(a)+1):
        for j in range(len(a)+1):
            for k in range(len(a)+1):
                for l in range(len(a)+1):
                    b = a[i:j] + a[k:l]
                    assert patch(a, diff_sequence(a, b)) == b
                    assert patch(b, diff_sequence(b, a)) == a

    #print("\n".join(map(repr, diff_sequence(a, b))))
