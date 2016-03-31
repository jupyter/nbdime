# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import pytest
import copy
import nbformat

from nbdime import merge_notebooks, merge, diff, patch
from nbdime.merging.notebooks import autoresolve
from nbdime.diff_format import make_op
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
    base = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
    local = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
    remote = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(7))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
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
    actual, lco, rco = merge_notebooks(base, local, remote, args)
    assert not lco
    assert not rco
    assert actual == expected


def test_merge_cell_sources_separate_inserts():
    base = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
    local = sources_to_notebook([[
        "print(f(3))",
        ], [
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
    remote = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ])
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
    actual, lco, rco = merge_notebooks(base, local, remote, args)
    assert not lco
    assert not rco
    assert actual == expected


def test_merge_cell_sources_conflicts_shift_indices_correctly():

    # Triplets of (local, base, remote) cell source strings
    cases = [
        ("same", "same", "different"), # no conflict, but will shift diff index
        ("left", "middle", "right"),   # conflict
        ("different", "same", "same"), # no conflict
        ]
    local  = sources_to_notebook([[case[0]] for case in cases])
    base   = sources_to_notebook([[case[1]] for case in cases])
    remote = sources_to_notebook([[case[2]] for case in cases])

    expected_partial = sources_to_notebook([
        ["different"], # autoresolved
        ["middle"],    # conflict remaining
        ["different"], # autoresolved
        ])
    expected_lco = [
        make_op("removerange", 1, 1),
        make_op("addrange", 1, ["left"]),
        ]
    expected_rco = [
        make_op("removerange", 1, 1),
        make_op("addrange", 1, ["right"]),
        ]

    args = None
    partial, lco, rco = merge_notebooks(base, local, remote, args)
    sources = [cell["source"] for cell in partial["cells"]]
    expected_sources = [cell["source"] for cell in expected_partial["cells"]]
    assert sources == expected_sources
    assert partial == expected_partial
    assert lco == expected_lco
    assert rco == expected_rco


def _check(base, local, remote, expected_partial, expected_lco, expected_rco):
    if isinstance(local, list):
        local  = sources_to_notebook(local)
    if isinstance(base, list):
        base   = sources_to_notebook(base)
    if isinstance(remote, list):
        remote = sources_to_notebook(remote)
    if isinstance(expected_partial, list):
        expected_partial = sources_to_notebook(expected_partial)

    args = None
    partial, lco, rco = merge_notebooks(base, local, remote, args)

    sources = [cell["source"] for cell in partial["cells"]]
    expected_sources = [cell["source"] for cell in expected_partial["cells"]]
    assert sources == expected_sources

    assert partial == expected_partial
    assert lco == expected_lco
    assert rco == expected_rco


def test_merge_single_cell_sources_conflicts():
    # A very basic test: Just checking changes to a single cell source,

    # No change
    local  = [["same"]]
    base   = [["same"]]
    remote = [["same"]]
    expected_partial = [["same"]]
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # One sided change
    local  = [["same"]]
    base   = [["same"]]
    remote = [["different"]]
    expected_partial = [["different"]]
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # One sided change
    local  = [["different"]]
    base   = [["same"]]
    remote = [["same"]]
    expected_partial = [["different"]]
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # Same change on both sides
    local  = [["different"]]
    base   = [["same"]]
    remote = [["different"]]
    expected_partial = [["different"]]
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # Completely changing cell on both sides interpreted as two new cell inserts, local first
    local  = [["local"]]
    base   = [["base"]]
    remote = [["remote"]]
    expected_partial = [["local"], ["remote"]]  # two cells!
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # Modifying cell on both sides interpreted as editing the original cell
    # (this is where heuristics kick in: when is a cell modified and when is it replaced?)
    source = [
        "def foo(x, y):",
        "    z = x * y",
        "    return z",
        ]
    local  = [source + ["local"]]
    base   = [source]
    remote = [source + ["remote"]]
    expected_partial = [source + ["local", "remote"]]  # one cell!
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # Modifying cell on both sides interpreted as editing the original cell,
    # but also one-sided inserts of new cells that shift cell indices
    source = [
        "def foo(x, y):",
        "    z = x * y",
        "    return z",
        ]
    local  = [["new local cell"], source + ["local"]]
    base   = [source]
    remote = [source + ["remote"], ["new remote cell"]]
    expected_partial = [["new local cell"],
                        source + ["local", "remote"],
                        ["new remote cell"]]
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)

    # FIXME: Code is perhaps too accepting, it's hard to make conflicts!
    # Conflicting modifications of cell on both sides,
    # but also one-sided inserts of new cells that shift cell indices
    source = [
        "def foo(x, y):",
        "    z = x * y",
        "    return z",
        ]
    local  = [["new local cell"], source]  # inserts cell at beginning and deletes line from base cell
    base   = [source + ["original"]]
    remote = [source + ["original2"], ["new remote cell"]]  # modifies line in base cell and inserts cell at end
    expected_partial = [["new local cell"],
                        source + ["original2"], # This should rather be original and include conflicts!
                        ["new remote cell"]]
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)


    # Trying to induce conflicts with shifting of diff indices
    local  = [["local 1"],  ["base 1"], ["local 2"], ["base 2"], ["local 3"],  ["base 3"], ["base 4"]]
    base   = [              ["base 1"],              ["base 2"],               ["base 3"], ["base 4"]]
    remote = [["remote 1"], ["base 1"], ["remote 2"],            ["remote 3"], ["base 3"]]
    expected_partial = [["local 1"], ["remote 1"], ["base 1"],
                        ["local 2"], ["remote 2"],
                        ["remote 3"], ["local 3"], ["base 3"]]  # in this case "remote 3" is before "local 3" because it's lumped together with "remote 2"
    expected_lco = []
    expected_rco = []
    _check(base, local, remote, expected_partial, expected_lco, expected_rco)
