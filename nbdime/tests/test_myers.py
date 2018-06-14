# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import operator
from six.moves import xrange as range

from nbdime.diffing.seq_myers import diff_sequence_myers, myers_ses



def xtest_lcs():
    # Both empty
    assert list(lcs([], [])) == []

    # One empty
    for i in range(10):
        a = list(range(i))
        assert list(lcs(a, [])) == []
        assert list(lcs([], a)) == []

    # Equal
    for i in range(0, 10):
        a = list(range(i))
        assert list(lcs(a, a)) == a

    # Delete any single item
    for i in range(10):
        a = list(range(i))
        for j in range(len(a)):
            b = list(a)
            b.pop(j)
            assert list(lcs(a, b)) == b

    # Delete successive interleaved items
    for i in range(1, 10):
        a = list(range(i))
        b = list(a)
        for j in range(len(a)-1, 0, -2):
            b.pop(j)
            assert list(lcs(a, b)) == b

    # Insert single item anywhere
    for i in range(10):
        a = list(range(i))
        for j in range(len(a)):
            b = list(a)
            b.insert(j, 77)
            assert list(lcs(a, b)) == a

    # Insert successive interleaved items
    for i in range(1, 10):
        a = list(range(i))
        b = list(a)
        for j in range(len(a)-1, 0, -2):
            b.insert(j, len(a) + j + 1)
            assert list(lcs(a, b)) == a


def test_myers_with_paper_case():
    # Case from neil.fraser.name/writing/diff/
    assert list(myers_ses(list("abcabba"), list("cbabac"))) == [-1, 1, 0, -1, 0, 0, -1, 0, 1]


def test_myers_with_neil_fraser_cases():
    # Case from neil.fraser.name/writing/diff/
    assert list(myers_ses(list("abcab"), list("ayb"))) == [-1, -1, -1, 0, 1]
    #assert greedy_forward_ses() == 3+1
    #assert greedy_reverse_ses(list("abcab"), list("ayb")) == 3+1
    #assert greedy_forward_ses(list("xaxcxabc"), list("abcy")) == 5+1
    #assert greedy_reverse_ses(list("xaxcxabc"), list("abcy")) == 5+1


def xtest_neil_fraser_case():
    # Case from neil.fraser.name/writing/diff/
    #assert list(lcs(list("abcab"), list("ayb"))) == ["a","b"]

    # These cases fail:
    assert list(lcs(list("abcab"), list("ayb"))) == ["a", "b"]
    #assert list(lcs(list("abcb"), list("ayb"))) == ["a","b"]

    # These cases work:
    #assert list(lcs(list("abyb"), list("ayb"))) == ["a","y","b"]
    #assert list(lcs(list("ayb"), list("ayb"))) == ["a","y","b"]
