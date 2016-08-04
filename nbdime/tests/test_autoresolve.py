# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import pytest

from nbdime import diff, merge_notebooks
from nbdime.diff_format import op_patch, op_replace
from nbdime.merging.autoresolve import autoresolve
from nbdime.merging.autoresolve import (
    make_cleared_value, add_conflicts_record, make_inline_source_value)


# Tests here assume default autoresolve behaviour at time of writing,
# this is likely to change and it's ok to update the tests to reflect
# new behaviour as needed!


def test_autoresolve_cleared_value():
    assert make_cleared_value(4) is None
    assert make_cleared_value([3]) == []
    assert make_cleared_value({1: 2}) == {}
    assert make_cleared_value("hello") == ""


def test_autoresolve_conflicts_record():
    assert add_conflicts_record({"a": 1}, [2], None) == {
        "a": 1, "nbdime-conflicts": {"local": [2]}}
    assert add_conflicts_record({"a": 1}, None, [3]) == {
        "a": 1, "nbdime-conflicts": {"remote": [3]}}
    assert add_conflicts_record({"a": 1}, [2], [3]) == {
        "a": 1, "nbdime-conflicts": {"local": [2], "remote": [3]}}


def test_autoresolve_inline_source():
    value = """\
def hello():
    print("world!")
"""
    le = op_patch("source", [op_replace(24, 'W')])  # FIXME: Character based here, should be linebased?
    re = op_patch("source", [op_replace(29, '.')])
    expected = """\
<<<<<<< local
def hello():
    print("World!")
======= base
def hello():
    print("world!")
======= remote
def hello():
    print("world.")
>>>>>>>
"""
    actual = make_inline_source_value(value, le, re)
    print(actual)
    assert actual == expected

    # FIXME: Add cases!


def xtest_autoresolve_inline_outputs():
    #value =
    #le =
    #re =
    #expected =
    #assert make_inline_outputs_value(value, le, re) == expected
    pass


def xtest_autoresolve_join():
    #value =
    #le =
    #re =
    #expected =
    #assert make_join_value(value, le, re) == expected
    pass


# These are reused in all tests below
args = None
base = {"foo": 1}
local = {"foo": 2}
remote = {"foo": 3}


def xtest_autoresolve_fail():
    # Check that "fail" strategy results in proper exception raised
    strategies = {"/foo": "fail"}
    with pytest.raises(RuntimeError):
        autoresolve(base, diff(base, local), diff(base, remote),
                    args, strategies, "")

    # Check that fallback to root "fail" strategy works the same way
    # strategies = { "": "fail" }
    # with pytest.raises(RuntimeError):
    #     autoresolve(base, diff(base, local), diff(base, remote),
    #                 args, strategies, "")


def xtest_autoresolve_invalidate():
    # Check strategies invalidate and use-*
    strategies = {"/foo": "invalidate"}
    merged, local_conflicts, remote_conflicts = autoresolve(
        base, diff(base, local), diff(base, remote), args, strategies, "")
    assert merged == {"foo": None}
    assert local_conflicts == []
    assert remote_conflicts == []


def xtest_autoresolve_use_one():
    strategies = {"/foo": "use-base"}
    merged, local_conflicts, remote_conflicts = autoresolve(
        base, diff(base, local), diff(base, remote), args, strategies, "")
    assert local_conflicts == []
    assert remote_conflicts == []
    assert merged == {"foo": 1}

    strategies = {"/foo": "use-local"}
    merged, local_conflicts, remote_conflicts = autoresolve(
        base, diff(base, local), diff(base, remote), args, strategies, "")
    assert merged == {"foo": 2}
    assert local_conflicts == []
    assert remote_conflicts == []

    strategies = {"/foo": "use-remote"}
    merged, local_conflicts, remote_conflicts = autoresolve(
        base, diff(base, local), diff(base, remote), args, strategies, "")
    assert merged == {"foo": 3}
    assert local_conflicts == []
    assert remote_conflicts == []


def xtest_autoresolve_notebook_ec():
    # Tests here assume default autoresolve behaviour at time of writing,
    # this may change and tests should then be updated
    source = "def foo(x, y):\n    return x**y"
    base = {"cells": [{"source": source, "execution_count": 1}]}
    local = {"cells": [{"source": source, "execution_count": 2}]}
    remote = {"cells": [{"source": source, "execution_count": 3}]}
    merged, decisions = merge_notebooks(base, local, remote, args)
    assert merged == {"cells": [{"source": source, "execution_count": None}]}
    assert not any([d.conflict for d in decisions])
