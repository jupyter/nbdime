# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import colorama
import pytest

from nbdime import merge_notebooks
from nbdime.merging.decisions import merge, apply_decisions
from nbdime.merging.autoresolve_decisions import autoresolve_decisions


colorama.init()

# FIXME: Extend tests to more merge situations!


# Tests here assume default autoresolve behaviour at time of writing,
# this is likely to change and it's ok to update the tests to reflect
# new behaviour as needed!


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


base = {"foo": 1}
local = {"foo": 2}
remote = {"foo": 3}
conflicted_decisions = merge(base, local, remote)


def test_autoresolve_fail():
    """Check that "fail" strategy results in proper exception raised."""
    strategies = {"/foo": "fail"}
    with pytest.raises(RuntimeError):
        autoresolve_decisions(base, conflicted_decisions, strategies)

    base2 = {"foo": {"bar": 1}}
    local2 = {"foo": {"bar": 2}}
    remote2 = {"foo": {"bar": 3}}
    strategies = {"/foo/bar": "fail"}
    decisions = merge(base2, local2, remote2)
    with pytest.raises(RuntimeError):
        autoresolve_decisions(base2, decisions, strategies)
    strategies = {"/foo": "fail"}
    with pytest.raises(RuntimeError):
        autoresolve_decisions(base2, decisions, strategies)


def test_autoresolve_clear():
    """Check strategy "clear" in various cases."""

    base2 = {"foo": [1, 2]}
    local2 = {"foo": [1, 4, 2]}
    remote2 = {"foo": [1, 3, 2]}
    decisions = merge(base2, local2, remote2)
    assert apply_decisions(base2, decisions) == {"foo": [1, 2]}
    assert decisions[0].local_diff != []
    assert decisions[0].remote_diff != []
    strategies = {"/foo": "clear-parent"}
    resolved = autoresolve_decisions(base2, decisions, strategies)
    assert apply_decisions(base2, resolved) == {"foo": []}
    assert not any([d.conflict for d in resolved])

    strategies = {"/foo": "clear"}
    resolved = autoresolve_decisions(base2, decisions, strategies)
    assert apply_decisions(base2, resolved) == {"foo": [1, None]}
    assert not any([d.conflict for d in resolved])


def test_autoresolve_use_one_side():
    strategies = {"/foo": "use-base"}
    decisions = autoresolve_decisions(base, conflicted_decisions, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": 1}

    strategies = {"/foo": "use-local"}
    decisions = autoresolve_decisions(base, conflicted_decisions, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": 2}

    strategies = {"/foo": "use-remote"}
    decisions = autoresolve_decisions(base, conflicted_decisions, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": 3}

    base2 = {"foo": {"bar": 1}}
    local2 = {"foo": {"bar": 2}}
    remote2 = {"foo": {"bar": 3}}
    conflicted_decisions2 = merge(base2, local2, remote2)

    strategies = {"/foo/bar": "use-base"}
    decisions = autoresolve_decisions(base2, conflicted_decisions2, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base2, decisions) == {"foo": {"bar": 1}}

    strategies = {"/foo/bar": "use-local"}
    decisions = autoresolve_decisions(base2, conflicted_decisions2, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base2, decisions) == {"foo": {"bar": 2}}

    strategies = {"/foo/bar": "use-remote"}
    decisions = autoresolve_decisions(base2, conflicted_decisions2, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base2, decisions) == {"foo": {"bar": 3}}


def test_autoresolve_notebook_ec():
    # Tests here assume default autoresolve behaviour at time of writing,
    # this may change and tests should then be updated
    args = None

    source = "def foo(x, y):\n    return x**y"
    base = {"cells": [{
        "source": source, "execution_count": 1, "cell_type": "code",
        "outputs": None}]}
    local = {"cells": [{
        "source": source, "execution_count": 2, "cell_type": "code",
        "outputs": None}]}
    remote = {"cells": [{
        "source": source, "execution_count": 3, "cell_type": "code",
        "outputs": None}]}
    merged, decisions = merge_notebooks(base, local, remote, args)
    assert merged == {"cells": [{
        "source": source, "execution_count": None, "outputs": None,
        "cell_type": "code"}]}
    assert not any(d.conflict for d in decisions)
