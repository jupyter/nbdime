# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.



import pytest
import copy
import nbformat

from nbdime.diff_format import op_patch, op_addrange, op_removerange, op_replace
from .utils import sources_to_notebook, outputs_to_notebook, have_git, strip_cell_ids, new_cell_wo_id, deterministic_cell_ids
from nbdime.nbmergeapp import _build_arg_parser
from nbdime import merge_notebooks, apply_decisions
from nbdime.diffing.notebooks import diff_notebooks, set_notebook_diff_targets
from nbdime.merging.notebooks import decide_merge_with_diff, Strategies

# FIXME: Extend tests to more merge situations!


# Setup default args for merge app
builder = _build_arg_parser()
args = builder.parse_args(["", "", ""])


def test_merge_matching_notebooks(matching_nb_triplets, reset_log):
    "Test merge on pairs of notebooks with the same basename in the test suite."
    base, local, remote = matching_nb_triplets
    merge_notebooks(base, local, remote)
    # We can't really automate a generic merge test,
    # at least passing through code here...


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

    assert merged == expected
    assert not any(d.conflict for d in decisions)


def test_merge_cell_sources_neighbouring_inserts_mergetool():
    base = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    local = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    remote = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "print(f(7))",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    expected_partial = base
    expected_conflicts = [{
        "common_path": ("cells",),
        "local_diff": [op_addrange(1, [local.cells[1]])],
        "remote_diff": [op_addrange(1, [remote.cells[1]])]
    }]

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_cell_sources_neighbouring_inserts_union():
    base = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    local = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    remote = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "print(f(7))",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    expected_partial = sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "print(f(7))",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ])
    expected_conflicts = []

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "union"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_cell_sources_separate_inserts():
    base = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    local = strip_cell_ids(sources_to_notebook([[
        "print(f(3))",
        ], [
        "def f(x):\n",
        "    return x**2",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ],
        ]))
    remote = strip_cell_ids(sources_to_notebook([[
        "def f(x):\n",
        "    return x**2",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ]))
    expected = strip_cell_ids(sources_to_notebook([[
        "print(f(3))",
        ], [
        "def f(x):\n",
        "    return x**2",
        ], [
        "def g(y):\n",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ]))
    actual, decisions = merge_notebooks(base, local, remote, args)
    assert not any([d.conflict for d in decisions])
    assert actual == expected


def src2nb(src, strip_ids=False):
    """Convert source strings to a notebook.

    src is either a single multiline string to become one cell,
    or a list (cells) of lists (lines) of singleline strings.
    """
    if isinstance(src, str):
        src = [[src]]
    if isinstance(src, list):
        src = sources_to_notebook(src)
    assert isinstance(src, dict)
    assert "cells" in src
    if strip_ids:
        strip_cell_ids(src)
    else:
        deterministic_cell_ids(src)
    return src


def _check(partial, expected_partial, decisions, expected_conflicts):
    sources = [cell.pop("source") for cell in partial["cells"]]
    expected_sources = [cell.pop("source") for cell in expected_partial["cells"]]
    assert sources == expected_sources

    outputs = [cell.pop("outputs") for cell in partial["cells"]]
    expected_outputs = [cell.pop("outputs") for cell in expected_partial["cells"]]
    assert outputs == expected_outputs

    assert partial == expected_partial
    conflicts = [d for d in decisions if d.conflict]
    expected_conflicts = copy.copy(expected_conflicts)
    assert len(conflicts) == len(expected_conflicts)
    for e, d in zip(expected_conflicts, conflicts):
        # Only check keys specified in expectation value
        for k in sorted(e.keys()):
            assert d[k] == e[k]


def _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args=None, ignore_cell_ids=False):
    base = src2nb(base, strip_ids=ignore_cell_ids)
    local = src2nb(local, strip_ids=ignore_cell_ids)
    remote = src2nb(remote, strip_ids=ignore_cell_ids)
    expected_partial = src2nb(expected_partial, strip_ids=ignore_cell_ids)
    merge_args = merge_args or args

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    _check(partial, expected_partial, decisions, expected_conflicts)


def _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args=None, ignore_cell_ids=False):
    base = outputs_to_notebook(base, strip_ids=ignore_cell_ids)
    local = outputs_to_notebook(local, strip_ids=ignore_cell_ids)
    remote = outputs_to_notebook(remote, strip_ids=ignore_cell_ids)
    expected_partial = outputs_to_notebook(expected_partial, strip_ids=ignore_cell_ids)
    merge_args = merge_args or args

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    _check(partial, expected_partial, decisions, expected_conflicts)


def test_merge_simple_cell_source_no_change():
    # A very basic test: Just checking changes to a single cell source,

    # No change
    local = [["same"]]
    base = [["same"]]
    remote = [["same"]]
    expected_partial = [["same"]]
    expected_conflicts = []
    _check_sources(base, local, remote, expected_partial, expected_conflicts, ignore_cell_ids=True)


def test_merge_simple_cell_source_remote_change():
    # One sided change
    local = [["same"]]
    base = [["same"]]
    remote = [["different"]]
    expected_partial = [["different"]]
    expected_conflicts = []
    _check_sources(base, local, remote, expected_partial, expected_conflicts, ignore_cell_ids=True)


def test_merge_simple_cell_source_local_change():
    # One sided change
    local = [["different"]]
    base = [["same"]]
    remote = [["same"]]
    expected_partial = [["different"]]
    expected_conflicts = []
    _check_sources(base, local, remote, expected_partial, expected_conflicts, ignore_cell_ids=True)


def test_merge_simple_cell_source_agreed_change():
    # Same change on both sides
    local = [["different"]]
    base = [["same"]]
    remote = [["different"]]
    expected_partial = [["different"]]
    expected_conflicts = []
    _check_sources(base, local, remote, expected_partial, expected_conflicts, ignore_cell_ids=True)


def test_merge_simple_cell_source_conflicting_edit_aligned():
    # Conflicting edit in first line of single cell
    local = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial = [["base\n", "some other\n", "lines\n", "to align\n"]]
    expected_conflicts = [{
        "common_path": ("cells", 0, "source"),
        "local_diff": [
            op_addrange(
                0, local[0][0:1]),
            op_removerange(0, 1)],
        "remote_diff": [
            op_addrange(
                0, remote[0][0:1]),
            op_removerange(0, 1)]
        }]
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


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
                1, [new_cell_wo_id(local[1][0])]),
            ],
            "remote_diff": [op_addrange(
                1, [new_cell_wo_id(remote[1][0])]),
            ]
        }]
    else:  # Treat as non-conflict (insert both)
        expected_partial = [["base"], ["local"], ["remote"]]
        expected_conflicts = []

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_multiline_cell_source_conflict():
    # Modifying cell on both sides interpreted as editing the original cell
    # Note: This only works with cell ids hinting that the cells are the same
    source = [
        "def foo(x, y):\n",
        "    z = x * y\n",
        "    return z\n",
        ]
    local = [source + ["local\n"] + [""]]
    base = [source + [""]]
    remote = [source + ["remote\n"] + [""]]

    le = op_addrange(3, ["local\n"])
    re = op_addrange(3, ["remote\n"])

    expected_partial = base
    expected_conflicts = [{
        "common_path": ("cells", 0, "source"),
        "local_diff": [le],
        "remote_diff": [re]
    }]
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args)


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
                op_addrange(0, [new_cell_wo_id(
                    source=["new local cell"])]),
                op_patch(0, [op_patch("source", [
                    op_addrange(len("".join(source)), "local\n")])]),
            ],
            "remote_diff": [op_patch(0, [op_patch('source', [
                op_addrange(len("".join(source)), "remote\n")])])]
        }]
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_interleave_cell_add_remove():
    # Interleaving cell inserts and deletes
    # no modifications = avoids heuristics
    local = [["local 1\n"],
             ["base 1\n"],
             ["local 2\n"],
             ["base 2\n"],
             ["local 3\n"],
             ["base 3\n"],
             ["base 4\n"]]
    base = [["base 1\n"],
            ["base 2\n"],
            ["base 3\n"],
            ["base 4\n"]]
    remote = [["remote 1\n"],
              ["base 1\n"],
              ["remote 2\n"],
              ["remote 3\n"],
              ["base 3\n"]]
    # Note: in this case "remote 3" is before "local 3" because it's lumped
    # together with "remote 2" in the diff and the insert of
    # ["remote 2", "remote 3"]starts before the removal of "base 2"
    expected_partial = [["local 1\n"],
                        ["remote 1\n"],
                        ["base 1\n"],
                        ["local 2\n"],
                        ["remote 2\n"],
                        ["remote 3\n"],
                        ["local 3\n"],
                        ["base 3\n"]]
    expected_conflicts = []

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "union"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_conflicts_get_diff_indices_shifted():
    # Trying to induce conflicts with shifting of diff indices
    source = [
        "def foo(x, y):\n",
        "    z = x * y\n",
        "    return z\n",
        ]
    local = [["same"], source + ["local\n"], ["different"]]
    base = [["same"], source + ["base\n"], ["same"]]
    remote = [["different"], source + ["remote\n"], ["same"]]
    expected_partial = [["different"],
                        source + ["base\n"],
                        ["different"]]
    expected_conflicts = [{
        "common_path": ('cells', 1, 'source'),
        "local_diff": [
            op_addrange(3, ["local\n"]),
            op_removerange(3, 1),
        ],
        "remote_diff": [
            op_addrange(3, ["remote\n"]),
            op_removerange(3, 1),
        ]
    }]

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args)

    # Trying to induce conflicts with shifting of diff indices
    local = [["same"],
             source + ["long line with minor change left"],
             ["different"]]
    base = [["same"],
            source + ["long line with minor change"],
            ["same"]]
    remote = [["different"],
              source + ["long line with minor change right"],
              ["same"]]
    expected_partial = [["different"],
                        source + ["long line with minor change"],
                        ["different"]]
    expected_conflicts = [{
        "common_path": ('cells', 1, 'source', 3),
        "local_diff": [
            op_addrange(27, " left"),
        ],
        "remote_diff": [
            op_addrange(27, " right"),
        ]
    }]
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args)


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
    _check_sources(base, local, remote, expected_partial, expected_conflicts)

    # Keep it failing
    assert False


def test_merge_input_strategy_local_source_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial = [["local\n", "some other\n", "lines\n", "to align\n"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.input_strategy = "use-local"
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_input_strategy_remote_source_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.input_strategy = "use-remote"
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_input_strategy_base_source_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial = [["base\n", "some other\n", "lines\n", "to align\n"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.input_strategy = "use-base"
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_input_strategy_union_source_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial = [["local\n", "remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.input_strategy = "union"
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args)


def test_merge_input_strategy_inline_source_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    # Ideal case:
    if have_git:
        expected_partial = [[
            "<<<<<<< local\n",
            "local\n",
            "=======\n",
            "remote\n",
            ">>>>>>> remote\n",
            "some other\n",
            "lines\n",
            "to align\n",
            ]]
    else:
        # Fallback is not very smart yet:
        expected_partial = [[
            "<<<<<<< local\n",
            "local\n",
            "some other\n",
            "lines\n",
            "to align\n",
            #'||||||| base\n',
            #'base\n',
            #'some other\n',
            #'lines\n',
            #'to align\n',
            "=======\n",
            "remote\n",
            "some other\n",
            "lines\n",
            "to align\n",
            ">>>>>>> remote",
            ]]
    expected_conflicts = [{
        "common_path": ("cells", 0, "source"),
        "local_diff": [
            op_addrange(0, local[0][0:1]),
            op_removerange(0, 1)
            ],
        "remote_diff": [
            op_addrange(0, remote[0][0:1]),
            op_removerange(0, 1)
            ],
        "custom_diff": [
            op_addrange(0, expected_partial[0]),
            op_removerange(0, len(base[0]))
            ],
        }]
    expected_conflicts = [{
        "common_path": ("cells", 0),
        "conflict": True,
        "action": "custom",
        "local_diff": [op_patch("source", [
            op_addrange(0, local[0][0:1]),
            op_removerange(0, 1)
            ])],
        "remote_diff": [op_patch("source", [
            op_addrange(0, remote[0][0:1]),
            op_removerange(0, 1)
            ])],
        "custom_diff": [op_replace("source", "".join(expected_partial[0]))],
        }]
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "use-base"
    merge_args.input_strategy = "inline"
    _check_sources(base, local, remote, expected_partial, expected_conflicts, merge_args, ignore_cell_ids=True)


def test_merge_output_strategy_local_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_partial = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.output_strategy = "use-local"
    _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_output_strategy_remote_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_partial = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.output_strategy = "use-remote"
    _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_output_strategy_base_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_partial = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.output_strategy = "use-base"
    _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_output_strategy_union_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_partial = [["local\nremote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.output_strategy = "union"
    _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_output_strategy_clear_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_partial = [["output2", "output3"]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.output_strategy = "remove"
    _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


def test_merge_output_strategy_clear_all_conflict():
    # Conflicting cell inserts at same location as removing old cell
    local = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]
    expected_partial = [[]]
    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.output_strategy = "clear-all"
    _check_outputs(base, local, remote, expected_partial, expected_conflicts, merge_args, True)


# TODO: Make test for output_strategy == 'inline'


def _make_notebook_with_multi_conflicts(
        expected_partial_source,
        expected_partial_metadata,
        expected_partial_outputs,
        ):
    local_source = [["local\n", "some other\n", "lines\n", "to align\n"]]
    base_source = [["base\n", "some other\n", "lines\n", "to align\n"]]
    remote_source = [["remote\n", "some other\n", "lines\n", "to align\n"]]

    local_metadata = [{'myval': 'local'}]
    base_metadata = [{'myval': 'base'}]
    remote_metadata = [{'myval': 'remote'}]

    local_outputs = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base_outputs = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    remote_outputs = [["remote\nsome other\nlines\nto align\n", "output2", "output3"]]

    base = outputs_to_notebook(base_outputs)
    local = outputs_to_notebook(local_outputs)
    remote = outputs_to_notebook(remote_outputs)
    expected_partial = outputs_to_notebook(expected_partial_outputs)

    for i in range(len(base.cells)):
        base.cells[i].source = "".join(base_source[i])
        local.cells[i].source = "".join(local_source[i])
        remote.cells[i].source = "".join(remote_source[i])
        expected_partial.cells[i].source = "".join(expected_partial_source[i])

        base.cells[i].metadata = base_metadata[i]
        local.cells[i].metadata = local_metadata[i]
        remote.cells[i].metadata = remote_metadata[i]
        expected_partial.cells[i].metadata = expected_partial_metadata[i]

    return base, local, remote, expected_partial


def test_metadata_union_strategy_metadata():
    # Conflicting cell inserts at same location as removing old cell
    expected_partial_source = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial_metadata = [{'myval': 'localremote'}]
    expected_partial_outputs = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base, local, remote, expected_partial = _make_notebook_with_multi_conflicts(
        expected_partial_source, expected_partial_metadata, expected_partial_outputs
    )

    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "union"
    merge_args.input_strategy = "use-remote"
    merge_args.output_strategy = "use-local"

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    _check(partial, expected_partial, decisions, expected_conflicts)


def test_metadata_union_strategy_not_applied_immutable_on_dict():
    # Conflicting cell inserts at same location as removing old cell
    expected_partial_source = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial_metadata = [{'myval': 5}]
    expected_partial_outputs = [["local\nsome other\nlines\nto align\n", "output2", "output3"]]
    base, local, remote, expected_partial = _make_notebook_with_multi_conflicts(
        expected_partial_source, expected_partial_metadata, expected_partial_outputs
    )
    base.cells[0].metadata['myval'] = 5
    local.cells[0].metadata['myval'] = 22
    remote.cells[0].metadata['myval'] = 13

    expected_conflicts = [{
        'action': 'base',
        'common_path': ('cells', 0, 'metadata'),
        'conflict': True,
        'local_diff': [{'key': 'myval', 'op': 'replace', 'value': 22}],
        'remote_diff': [{'key': 'myval', 'op': 'replace', 'value': 13}]
    }]
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "union"
    merge_args.input_strategy = "use-remote"
    merge_args.output_strategy = "use-local"

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    _check(partial, expected_partial, decisions, expected_conflicts)


def test_merge_mix_strategies():
    # Conflicting cell inserts at same location as removing old cell
    expected_partial_source = [["remote\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial_metadata = [{'myval': 'local'}]
    expected_partial_outputs = [["local\nremote\nsome other\nlines\nto align\n", "output2", "output3"]]
    base, local, remote, expected_partial = _make_notebook_with_multi_conflicts(
        expected_partial_source, expected_partial_metadata, expected_partial_outputs
    )

    expected_conflicts = []
    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "use-local"
    merge_args.input_strategy = "use-remote"
    merge_args.output_strategy = "union"

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    _check(partial, expected_partial, decisions, expected_conflicts)


def test_autoresolve_empty_strategies():
    """Check that a autoresolve works with empty strategies"""
    expected_partial_source = [["base\n", "some other\n", "lines\n", "to align\n"]]
    expected_partial_metadata = [{'myval': 'base'}]
    expected_partial_outputs = [["base\nsome other\nlines\nto align\n", "output2", "output3"]]
    base, local, remote, expected_partial = _make_notebook_with_multi_conflicts(
        expected_partial_source, expected_partial_metadata, expected_partial_outputs
    )
    strip_cell_ids(base)
    strip_cell_ids(local)
    strip_cell_ids(remote)
    strip_cell_ids(expected_partial)

    expected_conflicts = [
        {
            'action': 'base',
            'common_path': ('cells', 0, 'source'),
            'conflict': True,
            'local_diff': [{'key': 0, 'op': 'addrange', 'valuelist': ['local\n']},
                           {'key': 0, 'length': 1, 'op': 'removerange'}],
            'remote_diff': [{'key': 0, 'op': 'addrange', 'valuelist': ['remote\n']},
                            {'key': 0, 'length': 1, 'op': 'removerange'}]
        },
        {
            'action': 'base',
            'common_path': ('cells', 0, 'outputs', 0, 'data', 'text/plain'),
            'conflict': True,
            'local_diff': [{'key': 0, 'op': 'addrange', 'valuelist': ['local\n']},
                           {'key': 0, 'length': 1, 'op': 'removerange'}],
            'remote_diff': [{'key': 0, 'op': 'addrange', 'valuelist': ['remote\n']},
                            {'key': 0, 'length': 1, 'op': 'removerange'}]
        },
        {
            'action': 'base',
            'common_path': ('cells', 0, 'metadata', 'myval'),
            'conflict': True,
            'local_diff': [{'key': 0, 'op': 'addrange', 'valuelist': ['local']},
                           {'key': 0, 'length': 1, 'op': 'removerange'}],
            'remote_diff': [{'key': 0, 'op': 'addrange', 'valuelist': ['remote']},
                            {'key': 0, 'length': 1, 'op': 'removerange'}]
        }
    ]

    # Since we cannot pass directly a strategies object, include copy of relevant code:
    local_diffs = diff_notebooks(base, local)
    remote_diffs = diff_notebooks(base, remote)

    strategies = Strategies()
    decisions = decide_merge_with_diff(
        base, local, remote,
        local_diffs, remote_diffs,
        strategies)

    partial = apply_decisions(base, decisions)

    _check(partial, expected_partial, decisions, expected_conflicts)


def test_only_sources(db, reset_notebook_diff, reset_log):
    base = db["mixed-conflicts--1"]
    local = db["mixed-conflicts--2"]
    remote = db["mixed-conflicts--3"]
    set_notebook_diff_targets(True, False, False, False)

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    assert len(decisions) > 0
    for d in decisions:
        path = d['common_path']
        # Still have some decisions on cell root, so avoid with len == 2 check
        assert len(path) == 2 or path[2] == 'source'


def test_only_outputs(db, reset_notebook_diff):
    base = db["mixed-conflicts--1"]
    local = db["mixed-conflicts--2"]
    remote = db["mixed-conflicts--3"]
    set_notebook_diff_targets(False, True, False, False)

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    assert len(decisions) > 0
    for d in decisions:
        path = d['common_path']
        # Still have some decisions on cell root, so avoid with len == 2 check
        assert len(path) == 2 or path[2] == 'outputs'


def test_only_metadata(db, reset_notebook_diff):
    base = db["mixed-conflicts--1"]
    local = db["mixed-conflicts--2"]
    remote = db["mixed-conflicts--3"]
    set_notebook_diff_targets(False, False, False, True)

    merge_args = copy.deepcopy(args)
    merge_args.merge_strategy = "mergetool"

    partial, decisions = merge_notebooks(base, local, remote, merge_args)

    assert len(decisions) > 0
    for d in decisions:
        path = d['common_path']
        # Still have some decisions on cell root, so avoid with len == 2 check
        assert (
            len(path) == 2 or
            path[0] == 'metadata' or
            path[2] == 'metadata' or
            path[4] == 'metadata'
        )

