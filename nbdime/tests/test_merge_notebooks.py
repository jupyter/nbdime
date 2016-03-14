# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import pytest
import copy
import nbformat

from nbdime import merge_notebooks, merge, diff, patch
from nbdime.merging.notebooks import autoresolve
from .fixtures import sources_to_notebook


# FIXME: Extend tests to more merge situations!


def test_autoresolve_fail():
    """Check that "fail" strategy results in proper exception raised."""

    base = { "foo": 1 }
    local = { "foo": 2 }
    remote = { "foo": 3 }
    strategies = { "/foo": "fail" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    with pytest.raises(RuntimeError):
        autoresolve(merged, local_diffs, remote_diffs, strategies, "")

    base = { "foo": {"bar":1} }
    local = { "foo": {"bar":2} }
    remote = { "foo": {"bar":3} }
    strategies = { "/foo/bar": "fail" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    with pytest.raises(RuntimeError):
        autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    strategies = { "/foo": "fail" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    with pytest.raises(RuntimeError):
        autoresolve(merged, local_diffs, remote_diffs, strategies, "")


def test_autoresolve_clear():
    """Check strategy "clear" in various cases."""

    base = { "foo": 1 }
    local = { "foo": 2 }
    remote = { "foo": 3 }
    strategies = { "/foo": "clear" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    assert merged == { "foo": 1 }
    assert local_diffs != []
    assert remote_diffs != []
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert resolved == { "foo": None }
    assert local_conflicts == []
    assert remote_conflicts == []

    #base = { "foo": [1] }
    #local = { "foo": [2] }
    #remote = { "foo": [3] }
    #strategies = { "/foo": "clear" }
    #merged, local_diffs, remote_diffs = merge(base, local, remote)
    #resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    #resolved = patch(merged, resolutions)
    # This isn't happening because merge passes without conflict by removing [1] and adding [2,3] to foo:
    #assert local_diffs != []
    #assert remote_diffs != []
    #assert merged == { "foo": [1] }
    #assert resolved == { "foo": [] }
    #assert local_conflicts == []
    #assert remote_conflicts == []


def test_autoresolve_use_one_side():
    base = { "foo": 1 }
    local = { "foo": 2 }
    remote = { "foo": 3 }

    strategies = { "/foo": "use-base" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert local_conflicts == []
    assert remote_conflicts == []
    assert resolved == { "foo": 1 }

    strategies = { "/foo": "use-local" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert local_conflicts == []
    assert remote_conflicts == []
    assert resolved == { "foo": 2 }

    strategies = { "/foo": "use-remote" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert local_conflicts == []
    assert remote_conflicts == []
    assert resolved == { "foo": 3 }


    base = { "foo": {"bar": 1} }
    local = { "foo": {"bar": 2} }
    remote = { "foo": {"bar": 3} }

    strategies = { "/foo/bar": "use-base" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert local_conflicts == []
    assert remote_conflicts == []
    assert resolved == { "foo": {"bar": 1 } }

    strategies = { "/foo/bar": "use-local" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert local_conflicts == []
    assert remote_conflicts == []
    assert resolved == { "foo": {"bar": 2 } }

    strategies = { "/foo/bar": "use-remote" }
    merged, local_diffs, remote_diffs = merge(base, local, remote)
    resolutions, local_conflicts, remote_conflicts = autoresolve(merged, local_diffs, remote_diffs, strategies, "")
    resolved = patch(merged, resolutions)
    assert local_conflicts == []
    assert remote_conflicts == []
    assert resolved == { "foo": {"bar": 3 } }


def test_autoresolve_notebook_ec():
    args = None
    # We need a source here otherwise the cells are not aligned
    source = "def foo(x, y):\n    return x**y"

    base = nbformat.v4.new_notebook()
    base["cells"].append(nbformat.v4.new_code_cell())
    base["cells"][0]["source"] = source
    base["cells"][0]["execution_count"] = 1

    local = copy.deepcopy(base)
    remote = copy.deepcopy(base)
    expected = copy.deepcopy(base)
    local["cells"][0]["execution_count"] = 2
    remote["cells"][0]["execution_count"] = 3
    expected["cells"][0]["execution_count"] = None
    
    merged, local_conflicts, remote_conflicts = merge_notebooks(base, local, remote, args)

    if 0:
        print()
        print(merged)
        print(local_conflicts)
        print(remote_conflicts)
        print()

    assert merged == expected
    assert local_conflicts == []
    assert remote_conflicts == []


def test_merge_cell_sources_neighbouring_inserts():
    base = [[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    local = [[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    remote = [[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(7))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    expected = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "print(f(7))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
    args = None
    actual, lco, rco = merge_notebooks(sources_to_notebook(base), sources_to_notebook(local), sources_to_notebook(remote), args)
    assert not lco
    assert not rco
    assert actual == expected


def test_merge_cell_sources_separate_inserts():
    base = [[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    local = [[
        "print(f(3))",
        ], [
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    remote = [[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ]
    expected = sources_to_notebook([[
        "print(f(3))",
        ], [
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ])
    args = None
    actual, lco, rco = merge_notebooks(sources_to_notebook(base), sources_to_notebook(local), sources_to_notebook(remote), args)
    assert not lco
    assert not rco
    assert actual == expected
