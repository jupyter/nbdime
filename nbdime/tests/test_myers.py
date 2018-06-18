# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import operator
from six.moves import xrange as range

from nbdime.diffing.seq_myers import diff_sequence_myers, myers_ses
from nbdime.patching import patch


def assert_resulting_patch(base, remote):
    diff = diff_sequence_myers(base, remote)
    print(diff)
    assert patch(base, diff) == remote


def test_myers_ses_with_paper_case():
    # Case from Myers paper
    assert list(myers_ses(list("abcabba"), list("cbabac"))) == [-1, 1, 0, -1, 0, 0, -1, 0, 1]


def test_myers_ses_with_neil_fraser_cases():
    # Case from neil.fraser.name/writing/diff/
    assert list(myers_ses(list("abcab"), list("ayb"))) == [-1, -1, -1, 0, 1, 0]
    assert list(myers_ses(list("xaxcxabc"), list("abcy"))) == [
        -1, -1, -1, -1, -1, 0, 0, 0, 1]
    assert list(myers_ses(list("bayb"), list("ayb"))) == [-1, 0, 0, 0]
    assert list(myers_ses(list("abyb"), list("ayb"))) == [0, -1, 0, 0]
    assert list(myers_ses(list("aybx"), list("ayb"))) == [0, 0, 0, -1]
    assert list(myers_ses(list("ayxb"), list("ayb"))) == [0, 0, -1, 0]


def test_myers_diff_neil_fraser_case():
    # Case from neil.fraser.name/writing/diff/
    assert_resulting_patch(list("abcab"), list("ayb"))
    assert_resulting_patch(list("abyb"), list("ayb"))
    assert_resulting_patch(list("ayb"), list("ayb"))
    assert_resulting_patch(list("abcb"), list("ayb"))

    assert_resulting_patch(list("xaxcxabc"), list("abcy"))


def test_myers_diff_paper_case():
    # Case from Myers paper
    assert_resulting_patch(list("abcabba"), list("cbabac"))
