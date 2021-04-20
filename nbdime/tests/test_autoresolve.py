# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.



from nbdime import merge_notebooks

from nbdime.nbmergeapp import _build_arg_parser

# FIXME: Extend tests to more merge situations!


# Tests here assume default autoresolve behaviour at time of writing,
# this is likely to change and it's ok to update the tests to reflect
# new behaviour as needed!


# Setup default args for merge app
builder = _build_arg_parser()


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


def test_autoresolve_notebook_no_ignore():
    args = builder.parse_args(["", "", ""])
    args.ignore_transients = False

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
        "source": source, "execution_count": 1, "outputs": None,
        "cell_type": "code"}]}
    assert decisions[0].conflict is True
    assert len(decisions) == 1


def test_autoresolve_notebook_no_ignore_fallback():
    args = builder.parse_args(["", "", ""])
    args.ignore_transients = False
    args.merge_strategy = 'use-remote'

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
        "source": source, "execution_count": 3, "outputs": None,
        "cell_type": "code"}]}
    assert not any(d.conflict for d in decisions)


def test_autoresolve_notebook_ignore_fallback():
    args = builder.parse_args(["", "", ""])
    args.ignore_transients = True
    args.merge_strategy = 'use-remote'

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


def test_autoresolve_inline_source_conflict(db, needs_git):
    nbb = db["inline-conflict--1"]
    nbl = db["inline-conflict--2"]
    nbr = db["inline-conflict--3"]

    args = builder.parse_args(["", "", ""])
    args.merge_strategy = 'inline'
    merged, decisions = merge_notebooks(nbb, nbl, nbr, args)

    # Has conflicts
    assert any(d.conflict for d in decisions)

    source = merged.cells[0].source

    expected = """\
x = 1
<<<<<<< local
y = 3
z = 4
print(x * y / z)
=======
q = 3.1
print(x + q)
>>>>>>> remote"""

    assert source == expected
