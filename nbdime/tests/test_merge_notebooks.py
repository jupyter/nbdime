# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import pytest
import copy
from six import string_types
import nbformat

from nbdime.diff_format import op_patch, op_addrange, op_removerange
from .fixtures import sources_to_notebook, matching_nb_triplets
from nbdime.merging.autoresolve import (
    make_inline_source_value, autoresolve)
from nbdime.nbmergeapp import _build_arg_parser
from nbdime import merge_notebooks

# FIXME: Extend tests to more merge situations!


# Setup default args for merge app
builder = _build_arg_parser()
args = builder.parse_args(["", "", ""])


def test_merge_matching_notebooks(matching_nb_triplets):
    "Test merge on pairs of notebooks with the same basename in the test suite."
    base, local, remote = matching_nb_triplets
    merge_notebooks(base, local, remote)
    # We can't really automate a generic merge test, at least passing through code here...


def test_autoresolve_notebook_ec():
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

    merged, decisions = merge_notebooks(base, local, remote, args)

    if 0:
        print()
        print(merged)
        print(decisions)
        print()

    assert merged == expected
    assert not any(d.conflict for d in decisions)


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
    if 1:
        expected_partial = base
        expected_conflicts = [{
            "common_path": ("cells",),
            "local_diff": [op_addrange(1, [local.cells[1]])],
            "remote_diff": [op_addrange(1, [remote.cells[1]])]
        }]
    else:
        # Strategy local_then_remote:
        expected_partial = sources_to_notebook([[
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
        expected_conflicts = []

    _check(base, local, remote, expected_partial, expected_conflicts)


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
    actual, decisions = merge_notebooks(base, local, remote, args)
    assert not any([d.conflict for d in decisions])
    assert actual == expected


def src2nb(src):
    """Convert source strings to a notebook.

    src is either a single multiline string to become one cell,
    or a list (cells) of lists (lines) of singleline strings.
    """
    if isinstance(src, string_types):
        src = [src.splitlines(True)]
    if isinstance(src, list):
        src = sources_to_notebook(src)
    assert isinstance(src, dict)
    assert "cells" in src
    return src


def _check(base, local, remote, expected_partial, expected_conflicts, merge_args=None):
    base = src2nb(base)
    local = src2nb(local)
    remote = src2nb(remote)
    expected_partial = src2nb(expected_partial)
    merge_args = merge_args or args

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    sources = [cell.pop("source") for cell in partial["cells"]]
    expected_sources = [cell.pop("source") for cell in expected_partial["cells"]]
    assert sources == expected_sources

    assert partial == expected_partial
    conflicts = [d for d in decisions if d.conflict]
    expected_conflicts = copy.copy(expected_conflicts)
    assert len(conflicts) == len(expected_conflicts)
    for e, d in zip(expected_conflicts, conflicts):
        # Only check keys specified in expectation value
        for k in e.keys():
            assert d[k] == e[k]


def test_merge_simple_cell_source_no_change():
    # A very basic test: Just checking changes to a single cell source,

    # No change
    local = [["same"]]
    base = [["same"]]
    remote = [["same"]]
    expected_partial = [["same"]]
    expected_conflicts = []
    _check(base, local, remote, expected_partial, expected_conflicts)


def test_merge_simple_cell_source_remote_change():
    # One sided change
    local = [["same"]]
    base = [["same"]]
    remote = [["different"]]
    expected_partial = [["different"]]
    expected_conflicts = []
    _check(base, local, remote, expected_partial, expected_conflicts)


def test_merge_simple_cell_source_local_change():
    # One sided change
    local = [["different"]]
    base = [["same"]]
    remote = [["same"]]
    expected_partial = [["different"]]
    expected_conflicts = []
    _check(base, local, remote, expected_partial, expected_conflicts)


def test_merge_simple_cell_source_agreed_change():
    # Same change on both sides
    local = [["different"]]
    base = [["same"]]
    remote = [["different"]]
    expected_partial = [["different"]]
    expected_conflicts = []
    _check(base, local, remote, expected_partial, expected_conflicts)


def test_merge_simple_cell_source_conflicting_edit_aligned():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local"]]
    base = [["base"]]
    remote = [["remote"]]
    expected_partial = [["base"]]
    expected_conflicts = [{
        "common_path": ("cells",),
        "local_diff": [
            op_addrange(
                0, [nbformat.v4.new_code_cell(source) for source in local]),
            op_removerange(0, 1)],
        "remote_diff": [
            op_addrange(
                0, [nbformat.v4.new_code_cell(source) for source in remote]),
            op_removerange(0, 1)]
        }]
    _check(base, local, remote, expected_partial, expected_conflicts)


def test_merge_simple_cell_source_conflicting_insert():
    # Cell inserts at same location but no other modifications:
    # should this be accepted?
    local = [["base"], ["local"]]
    base = [["base"]]
    remote = [["base"], ["remote"]]
    if 1:  # Treat as conflict
        expected_partial = [["base"]]
        expected_conflicts = [{
            "common_path": ("cells",),
            "local_diff": [op_addrange(
                1, [nbformat.v4.new_code_cell(local[1])]),
            ],
            "remote_diff": [op_addrange(
                1, [nbformat.v4.new_code_cell(remote[1])]),
            ]
        }]
    else:  # Treat as non-conflict (insert both)
        expected_partial = [["base"], ["local"], ["remote"]]
        expected_conflicts = []
    _check(base, local, remote, expected_partial, expected_conflicts)


@pytest.mark.xfail
def test_merge_multiline_cell_source_conflict():
    # Modifying cell on both sides interpreted as editing the original cell
    # (this is where heuristics kick in: when is a cell modified and when is
    # it replaced?)
    source = [
        "def foo(x, y):\n",
        "    z = x * y\n",
        "    return z\n",
        ]
    local = [source + ["local\n"] + [""]]
    base = [source + [""]]
    remote = [source + ["remote\n"] + [""]]

    le = op_addrange(3, "local\n")
    re = op_addrange(3, "remote\n")

    expected_partial = base
    expected_conflicts = [{
        "common_path": ("cells", "0", "source"),
        "local_diff": [le],
        "remote_diff": [re]
    }]
    _check(base, local, remote, expected_partial, expected_conflicts)


def test_merge_insert_cells_around_conflicting_cell():
    # Modifying an original cell and inserting a new cell on both sides
    source = [
        "def foo(x, y):\n",
        "    z = x * y\n",
        "    return z\n",
        ]
    local = [["new local cell\n"],
             source + ["local\n"]]
    base = [source]
    remote = [source + ["remote\n"],
              ["new remote cell\n"]]
    # Use mergetool strategy:
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"
    if 0:
        # This is how it would look if neither source or cell inserts resulted
        # in conflicts:
        expected_partial = [local[0],
                            source + ["local\n", "remote\n"],
                            remote[1]]
        expected_conflicts = []
    elif 1:
        # This is how it would look if source inserts but not cell inserts
        # resulted in conflicts:
        expected_partial = [local[0], source, remote[1]]
        expected_conflicts = [{
            "common_path": ("cells", 0, "source"),
            "local_diff": [op_addrange(len(source), ["local\n"])],
            "remote_diff": [op_addrange(len(source), ["remote\n"])]
        }]
    else:
        # In current behaviour:
        # - base cell 0 is aligned correctly (this is the notebook diff heuristics)
        # - conflicting edits of base cell 0 detected
        # - local insert before cell 0 is treated as part of conflict on base cell 0
        # - remote insert after cell 0 is not treated as part of conflict
        # FIXME: This may not be the exact behaviour we want:
        # - For source, we might want both inserts to be part of the conflict.
        #   (if so, fix in generic merge and chunk collection)
        # - For cells, we might want both inserts to be ok, they are separate new cells after all. (use autoresolve for this?)
        # - Figure out the best behaviour and make it happen!
        expected_partial = [source, remote[1]]
        expected_conflicts = [{
            "common_path": ("cells",),
            "local_diff": [
                op_addrange(0, [nbformat.v4.new_code_cell(
                    source=["new local cell"])]),
                op_patch(0, [op_patch("source", [
                    op_addrange(len("".join(source)), "local\n")])]),
            ],
            "remote_diff": [op_patch(0, [op_patch('source', [
                op_addrange(len("".join(source)), "remote\n")])])]
        }]
    _check(base, local, remote, expected_partial, expected_conflicts, merge_args)


@pytest.mark.xfail
def test_merge_interleave_cell_add_remove():
    # Interleaving cell inserts and deletes
    # no modifications = avoids heuristics
    local = [["local 1"],
             ["base 1"],
             ["local 2"],
             ["base 2"],
             ["local 3"],
             ["base 3"],
             ["base 4"]]
    base = [["base 1"],
            ["base 2"],
            ["base 3"],
            ["base 4"]]
    remote = [["remote 1"],
              ["base 1"],
              ["remote 2"],
              ["remote 3"],
              ["base 3"]]
    # Note: in this case "remote 3" is before "local 3" because it's lumped
    # together with "remote 2" in the diff and the insert of
    # ["remote 2", "remote 3"]starts before the removal of "base 2"
    expected_partial = [["local 1"],
                        ["remote 1"],
                        ["base 1"],
                        ["local 2"],
                        ["remote 2"],
                        ["remote 3"],
                        ["local 3"],
                        ["base 3"]]
    expected_conflicts = []
    _check(base, local, remote, expected_partial, expected_conflicts)


@pytest.mark.xfail
def test_merge_conflicts_get_diff_indices_shifted():
    # Trying to induce conflicts with shifting of diff indices
    source = [
        "def foo(x, y):",
        "    z = x * y",
        "    return z",
        ]
    local = [["same"], source+["local"], ["different"]]
    base = [["same"], source+["base"], ["same"]]
    remote = [["different"], source+["remote"], ["same"]]
    expected_partial = [["different"],
                        source + ["local", "remote"],
                        ["different"]]
    expected_conflicts = [{
        "common_path": (),
        "local_diff": [
            op_removerange(1, 1),
            op_addrange(1, ["left"]),
        ],
        "remote_diff": [
            op_removerange(1, 1),
            op_addrange(1, ["right"]),
        ]
    }]
    _check(base, local, remote, expected_partial, expected_conflicts)

    # Trying to induce conflicts with shifting of diff indices
    source = [
        "def foo(x, y):",
        "    z = x * y",
        "    return z",
        ]
    local = [["same"],
             source + ["long line with minor change L"],
             ["different"]]
    base = [["same"],
            source + ["long line with minor change"],
            ["same"]]
    remote = [["different"],
              source + ["long line with minor change R"],
              ["same"]]
    expected_partial = [["different"],
                        source + ["long line with minor change"],
                        ["different"]]
    expected_conflicts = [{
        "common_path": (),
        "local_diff": [
            op_removerange(1, 1),
            op_addrange(1, ["left"]),
        ],
        "remote_diff": [
            op_removerange(1, 1),
            op_addrange(1, ["right"]),
        ]
    }]
    _check(base, local, remote, expected_partial, expected_conflicts)


@pytest.mark.xfail
def test_merge_inserts_within_deleted_range():
    # Multiple inserts within a deleted range
    base = """
def f(x):
    return x**2

def g(x):
    return x + 2
"""

    # Insert foo and bar
    local = """
def foo(y):
    return y / 3

def f(x):
    return x**2

def bar(y):
    return y - 3

def g(x):
    return x + 2
"""

    remote = ""  # Delete all

    if 0:
        # This is quite optimistic and would require employing aggressive
        # attempts at automatic resolution beyond what git and meld do:
        expected_partial = """
def foo(y):
    return y / 3

def bar(y):
    return y - 3
"""
    else:
        expected_partial = base
        expected_conflicts = [{
            "common_path": ("cells",),
            "local_diff": [op_patch("cells", [op_addrange(0, [
                nbformat.v4.new_code_cell(local)]), op_removerange(0, 1)])],
            "remote_diff": [op_patch("cells", [op_addrange(0, [
                nbformat.v4.new_code_cell(remote)]), op_removerange(0, 1)])]
        }]
    _check(base, local, remote, expected_partial, expected_conflicts)

    # Keep it failing
    assert False
