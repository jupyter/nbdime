# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.



import pytest

from nbdime.diff_format import op_remove, op_patch
from nbdime.merging.decisions import (
    ensure_common_path, MergeDecisionBuilder, MergeDecision,
    pop_patch_decision, build_diffs,
)


# `ensure_common_path` tests:

def test_ensure_common_path_no_change():
    diffs = [[op_remove("c")], [op_patch("c", [op_remove("d")])]]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b"), diffs)


def test_ensure_common_path_single_level():
    diffs = [[op_patch("c", [op_remove("e")])],
             [op_patch("c", [op_remove("d")])]]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b", "c"), [[op_remove("e")], [op_remove("d")]])


def test_ensure_common_path_multilevel_leafs():
    diffs = [[op_patch("c", [op_patch("d", [op_remove("e")])])],
             [op_patch("c", [op_patch("d", [op_remove("f")])])]]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b", "c", "d"), [[op_remove("e")], [op_remove("f")]])


def test_ensure_common_path_multilevel_intermediate():
    diffs = [[op_patch("c", [op_patch("d", [op_remove("f")])])],
             [op_patch("c", [op_patch("e", [op_remove("g")])])]]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b", "c"), [[op_patch("d", [op_remove("f")])],
                                     [op_patch("e", [op_remove("g")])]])


def test_ensure_common_path_one_sided_none():
    diffs = [None,
             [op_patch("c", [op_remove("d")])]]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b", "c"), [None, [op_remove("d")]])


def test_ensure_common_path_one_sided_empty():
    diffs = [[],
             [op_patch("c", [op_remove("d")])]]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b", "c"), [None, [op_remove("d")]])


def test_ensure_common_path_one_sided_remote():
    diffs = [[op_patch("c", [op_remove("d")])],
             []]
    res = ensure_common_path(("a", "b"), diffs)
    assert res == (("a", "b", "c"), [[op_remove("d")], None])


# Here, just check that MergeDecisionBuilder uses ensure_common_path
def test_merge_builder_ensures_common_path():
    b = MergeDecisionBuilder()
    b.conflict(("a", "b"),
               [op_patch("c", [op_remove("d")])],
               [op_patch("c", [op_remove("e")])])
    assert len(b.decisions) == 1
    assert b.decisions[0].common_path == ("a", "b", "c")
    assert b.decisions[0].local_diff == [op_remove("d")]
    assert b.decisions[0].remote_diff == [op_remove("e")]


# `pop_patch` tests:

def test_pop_patch_unpoppable():
    md = MergeDecision(
        common_path=("a", "b"),
        action="base",
        conflict=True,
        local_diff=[op_remove("c")],
        remote_diff=[op_patch("c", [op_remove("d")])]
    )
    dec = pop_patch_decision(md)
    assert dec is None


def test_pop_patch_single_level():
    md = MergeDecision(
        common_path=("a", "b"),
        action="base",
        conflict=True,
        local_diff=[op_patch("c", [op_remove("d")])],
        remote_diff=[op_patch("c", [op_remove("e")])]
    )
    dec = pop_patch_decision(md)
    assert dec is not None
    assert dec.common_path == ("a", "b", "c")
    assert dec.local_diff == [op_remove("d")]
    assert dec.remote_diff == [op_remove("e")]


def test_pop_patch_multilevel():
    md = MergeDecision(
        common_path=("a", "b"),
        action="base",
        conflict=True,
        local_diff=[op_patch("c", [op_patch("d", [op_remove("e")])])],
        remote_diff=[op_patch("c", [op_patch("d", [op_remove("f")])])]
    )
    dec = pop_patch_decision(md)
    dec = pop_patch_decision(dec)
    assert dec.common_path == ("a", "b", "c", "d")
    assert dec.local_diff == [op_remove("e")]
    assert dec.remote_diff == [op_remove("f")]


@pytest.mark.xfail()
def test_build_diffs_unsorted():
    # expected to fail, since `validated` call is significant here!
    b = MergeDecisionBuilder()
    b.onesided((), [op_remove('a')], None)
    b.onesided(('b',), [op_remove('j')], None)
    b.onesided(('c',), [op_remove('k')], None)
    b.onesided(('d',), [op_remove('l')], None)
    base = dict(a=1, b=dict(i=2), c=dict(j=3), d=dict(k=4))
    diff = build_diffs(base, b.decisions, 'local')
    assert len(diff) == 4
    assert diff[0] == op_remove('a')
    assert diff[1] == op_patch('b', [op_remove('j')])
    assert diff[2] == op_patch('c', [op_remove('k')])
    assert diff[3] == op_patch('d', [op_remove('l')])


def test_build_diffs_sorted():
    b = MergeDecisionBuilder()
    b.onesided((), [op_remove('a')], None)
    b.onesided(('b',), [op_remove('j')], None)
    b.onesided(('c',), [op_remove('k')], None)
    b.onesided(('d',), [op_remove('l')], None)
    base = dict(a=1, b=dict(i=2), c=dict(j=3), d=dict(k=4))
    decisions = b.validated(base)
    diff = build_diffs(base, decisions, 'local')
    assert len(diff) == 4
    assert diff[0] == op_patch('d', [op_remove('l')])
    assert diff[1] == op_patch('c', [op_remove('k')])
    assert diff[2] == op_patch('b', [op_remove('j')])
    assert diff[3] == op_remove('a')

