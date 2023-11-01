# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest
import nbformat
from nbformat.v4 import new_notebook, new_code_cell
from collections import defaultdict

from nbdime import merge_notebooks, diff
from nbdime.diff_format import op_patch
from nbdime.utils import Strategies
from nbdime.diffing.config import DiffConfig
from nbdime.merging.generic import decide_merge, decide_merge_with_diff
from nbdime.merging.decisions import apply_decisions
from nbdime.merging.strategies import _cell_marker_format

from .utils import outputs_to_notebook, sources_to_notebook, strip_cell_ids, strip_cell_id


def test_decide_merge_strategy_fail(reset_log):
    """Check that "fail" strategy results in proper exception raised."""
    # One level dict
    base = {"foo": 1}
    local = {"foo": 2}
    remote = {"foo": 3}
    strategies = Strategies({"/foo": "fail"})
    with pytest.raises(RuntimeError):
        # pylint: disable=unused-variable
        conflicted_decisions = decide_merge(base, local, remote, strategies)

    # Nested dicts
    base = {"foo": {"bar": 1}}
    local = {"foo": {"bar": 2}}
    remote = {"foo": {"bar": 3}}
    strategies = Strategies({"/foo/bar": "fail"})
    with pytest.raises(RuntimeError):
        # pylint: disable=unused-variable
        decisions = decide_merge(base, local, remote, strategies)

    # We don't need this for non-leaf nodes and it's currently not implemented
    # strategies = Strategies({"/foo": "fail"})
    # with pytest.raises(RuntimeError):
    #     decisions = decide_merge(base, local, remote, strategies)


def test_decide_merge_strategy_clear1():
    """Check strategy "clear" in various cases."""
    # One level dict, clearing item value (think foo==execution_count)
    base = {"foo": 1}
    local = {"foo": 2}
    remote = {"foo": 3}
    strategies = Strategies({"/foo": "clear"})
    decisions = decide_merge(base, local, remote, strategies)
    assert apply_decisions(base, decisions) == {"foo": None}
    assert not any([d.conflict for d in decisions])

def test_decide_merge_strategy_clear2():
    base = {"foo": "1"}
    local = {"foo": "2"}
    remote = {"foo": "3"}
    strategies = Strategies({"/foo": "clear"})
    decisions = decide_merge(base, local, remote, strategies)
    #assert decisions == []
    assert apply_decisions(base, decisions) == {"foo": ""}
    assert not any([d.conflict for d in decisions])

    # We don't need this for non-leaf nodes and it's currently not implemented
    # base = {"foo": [1]}
    # local = {"foo": [2]}
    # remote = {"foo": [3]}
    # strategies = Strategies({"/foo": "clear"})
    # decisions = decide_merge(base, local, remote, strategies)
    # assert apply_decisions(base, decisions) == {"foo": []}
    # assert not any([d.conflict for d in decisions])


def test_decide_merge_strategy_clear_all():
    base = {"foo": [1, 2]}
    local = {"foo": [1, 4, 2]}
    remote = {"foo": [1, 3, 2]}

    strategies = Strategies({"/foo": "clear-all"})
    decisions = decide_merge(base, local, remote, strategies)
    assert apply_decisions(base, decisions) == {"foo": []}

    base = {"foo": [1, 2]}
    local = {"foo": [1, 4, 2]}
    remote = {"foo": [1, 2, 3]}

    strategies = Strategies({"/foo": "clear-all"})
    decisions = decide_merge(base, local, remote, strategies)
    assert apply_decisions(base, decisions) == {"foo": [1, 4, 2, 3]}


def test_decide_merge_strategy_remove():
    base = {"foo": [1, 2]}
    local = {"foo": [1, 4, 2]}
    remote = {"foo": [1, 3, 2]}

    strategies = Strategies({"/foo": "remove"})
    decisions = decide_merge(base, local, remote, strategies)
    assert apply_decisions(base, decisions) == {"foo": [1, 2]}
    assert decisions[0].local_diff != []
    assert decisions[0].remote_diff != []

    strategies = Strategies({})
    decisions = decide_merge(base, local, remote, strategies)
    assert apply_decisions(base, decisions) == {"foo": [1, 2]}
    assert decisions[0].local_diff != []
    assert decisions[0].remote_diff != []


def test_decide_merge_strategy_use_foo_on_dict_items():
    base = {"foo": 1}
    local = {"foo": 2}
    remote = {"foo": 3}

    strategies = Strategies({"/foo": "use-base"})
    decisions = decide_merge(base, local, remote, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": 1}

    strategies = Strategies({"/foo": "use-local"})
    decisions = decide_merge(base, local, remote, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": 2}

    strategies = Strategies({"/foo": "use-remote"})
    decisions = decide_merge(base, local, remote, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": 3}

    base = {"foo": {"bar": 1}}
    local = {"foo": {"bar": 2}}
    remote = {"foo": {"bar": 3}}

    strategies = Strategies({"/foo/bar": "use-base"})
    decisions = decide_merge(base, local, remote, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": {"bar": 1}}

    strategies = Strategies({"/foo/bar": "use-local"})
    decisions = decide_merge(base, local, remote, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": {"bar": 2}}

    strategies = Strategies({"/foo/bar": "use-remote"})
    decisions = decide_merge(base, local, remote, strategies)
    assert not any([d.conflict for d in decisions])
    assert apply_decisions(base, decisions) == {"foo": {"bar": 3}}


def test_decide_merge_simple_list_insert_conflict_resolution():
    # local and remote adds an entry each
    b = [1]
    l = [1, 2]
    r = [1, 3]

    strategies = Strategies({"/*": "use-local"})
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == l
    assert not any(d.conflict for d in decisions)

    strategies = Strategies({"/*": "use-remote"})
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == r
    assert not any(d.conflict for d in decisions)

    strategies = Strategies({"/*": "use-base"})
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == b
    assert not any(d.conflict for d in decisions)

    strategies = Strategies({"/": "clear-all"})
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == []
    assert not any(d.conflict for d in decisions)

def test_decide_merge_simple_list_insert_conflict_resolution__union():
    # local and remote adds an entry each
    b = [1]
    l = [1, 2]
    r = [1, 3]

    strategies = Strategies({"/": "union"})
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == [1, 2, 3]
    assert not any(d.conflict for d in decisions)


def test_decide_merge_list_conflicting_insertions_separate_chunks_v1():
    # local and remote adds an equal entry plus a different entry each
    # First, test when insertions DO NOT chunk together:
    b = [1, 9]
    l = [1, 2, 9, 11]
    r = [1, 3, 9, 11]

    # Check strategyless resolution
    strategies = Strategies({})
    resolved = decide_merge(b, l, r, strategies)
    expected_partial = [1, 9, 11]
    assert apply_decisions(b, resolved) == expected_partial
    assert len(resolved) == 2
    assert resolved[0].conflict
    assert not resolved[1].conflict

    strategies = Strategies({"/*": "use-local"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == l
    assert not any(d.conflict for d in resolved)

    strategies = Strategies({"/*": "use-remote"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == r
    assert not any(d.conflict for d in resolved)

    strategies = Strategies({"/*": "use-base"})
    resolved = decide_merge(b, l, r, strategies)
    # Strategy is only applied to conflicted decisions:
    assert apply_decisions(b, resolved) == expected_partial
    assert not any(d.conflict for d in resolved)

    strategies = Strategies({"/": "clear-all"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == []
    assert not any(d.conflict for d in resolved)

    # from _merge_concurrent_inserts:
    # FIXME: This function doesn't work out so well with new conflict handling,
    # when an insert (e.g. [2,7] vs [3,7]) gets split into agreement on [7] and
    # conflict on [2] vs [3], the ordering gets lost. I think this was always
    # slightly ambiguous in the decision format, as the new inserts will get
    # the same key and decisions are supposed to be possible to reorder (sort)
    # without considering original ordering of decisions. To preserve the
    # ordering, perhaps we can add relative local/remote indices to the decisions?
    # We had this, where ordering made it work out correctly:
    #   "conflicting insert [2] vs [3] at 1 (base index);
    #    insert [7] at 1 (base index)"
    # instead we now have this which messes up the ordering:
    #   "insert [7] at 1 (base index);
    #    conflicting insert [2] vs [3] at 1 (base index)"
    # perhaps change to this:
    #   "insert [7] at key=1 (base index) lkey=1 rkey=1;
    #    conflicting insert [2] vs [3] at key=1 (base index) lkey=0 rkey=0"
    # then decisions can be sorted on (key,lkey) or (key,rkey) depending on chosen side.
    # This test covers the behaviour:
    # py.test -k test_shallow_merge_lists_insert_conflicted -s -vv
    #DEBUGGING = 1
    #if DEBUGGING: import ipdb; ipdb.set_trace()

    # Example:
    # b  l  r
    # 1  a  x
    # 2  b  y
    # 3  c  3
    # 4  4  4
    # Diffs:
    # b/l: insert a, b, c; remove 1-3
    # b/r: insert x, y; remove 1-2
    # The current chunking splits the removes here:
    # [insert a, b, c; remove 1-2]; [remove 3]
    # [insert x, y; remove 1-2]
    # That results in remove 3 not being conflicted.

def test_decide_merge_list_conflicting_insertions_separate_chunks_v2():
    # local and remote adds an equal entry plus a different entry each
    # First, test when insertions DO NOT chunk together:
    b = [1, 9]
    l = [1, 2, 9, 11]
    r = [1, 3, 9, 11]

    # Check strategyless resolution
    strategies = Strategies({})
    resolved = decide_merge(b, l, r, strategies)
    expected_partial = [1, 9, 11]
    assert apply_decisions(b, resolved) == expected_partial
    assert len(resolved) == 2
    assert resolved[0].conflict
    assert not resolved[1].conflict


def test_decide_merge_list_conflicting_insertions_separate_chunks__union():
    # local and remote adds an equal entry plus a different entry each
    # First, test when insertions DO NOT chunk together:
    b = [1, 9]
    l = [1, 2, 9, 11]
    r = [1, 3, 9, 11]

    strategies = Strategies({"/": "union"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == [1, 2, 3, 9, 11]
    assert not any(d.conflict for d in resolved)


def test_decide_merge_list_conflicting_insertions_in_chunks():
    # Next, test when insertions DO chunk together:
    b = [1, 9]
    l = [1, 2, 7, 9]
    r = [1, 3, 7, 9]

    # Check strategyless resolution
    strategies = Strategies({})
    resolved = decide_merge(b, l, r, strategies)
    expected_partial = [1, 7, 9]
    assert apply_decisions(b, resolved) == expected_partial

    strategies = Strategies({"/*": "use-local"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == l
    assert not any(d.conflict for d in resolved)

    strategies = Strategies({"/*": "use-remote"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == r
    assert not any(d.conflict for d in resolved)

    strategies = Strategies({"/*": "use-base"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == expected_partial
    assert not any(d.conflict for d in resolved)

    strategies = Strategies({"/": "clear-all"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == []
    assert not any(d.conflict for d in resolved)


def test_decide_merge_list_conflicting_insertions_in_chunks__union():
    # Next, test when insertions DO chunk together:
    b = [1, 9]
    l = [1, 2, 7, 9]
    r = [1, 3, 7, 9]

    strategies = Strategies({"/": "union"})
    resolved = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, resolved) == [1, 2, 3, 7, 9]
    assert not any(d.conflict for d in resolved)


def test_decide_merge_list_transients():
    # For this test, we need to use a custom predicate to ensure alignment
    common = {'id': 'This ensures alignment'}
    config = DiffConfig(
        predicates=defaultdict(lambda: [operator.__eq__], {
            '/': [lambda a, b: a['id'] == b['id']],
        })
    )

    # Setup transient difference in base and local, deletion in remote
    b = [{'transient': 22}]
    l = [{'transient': 242}]
    b[0].update(common)
    l[0].update(common)
    r = []

    # Make decisions based on diffs with predicates
    ld = diff(b, l, path="", config=config)
    rd = diff(b, r, path="", config=config)

    # Assert that generic merge without strategies gives conflict:
    strategies = Strategies()
    decisions = decide_merge_with_diff(b, l, r, ld, rd, strategies)
    assert len(decisions) == 1
    assert decisions[0].conflict
    assert apply_decisions(b, decisions) == b

    # Supply transient list to autoresolve, and check that transient is ignored
    strategies = Strategies(transients=[
        '/*/transient'
    ])
    decisions = decide_merge_with_diff(b, l, r, ld, rd, strategies)
    assert apply_decisions(b, decisions) == r
    assert not any(d.conflict for d in decisions)


def test_decide_merge_dict_transients():
    # Setup transient difference in base and local, deletion in remote
    b = {'a': {'transient': 22}}
    l = {'a': {'transient': 242}}
    r = {}

    # Assert that generic merge gives conflict
    strategies = Strategies()
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == b
    assert len(decisions) == 1
    assert decisions[0].conflict

    # Supply transient list to autoresolve, and check that transient is ignored
    strategies = Strategies(transients=[
        '/a/transient'
    ])
    decisions = decide_merge(b, l, r, strategies)
    assert apply_decisions(b, decisions) == r
    assert not any(d.conflict for d in decisions)


def test_decide_merge_mixed_nested_transients():
    # For this test, we need to use a custom predicate to ensure alignment
    common = {'id': 'This ensures alignment'}
    config = DiffConfig(
        predicates=defaultdict(lambda: [operator.__eq__], {
            '/': [lambda a, b: a['id'] == b['id']],
        })
    )
    # Setup transient difference in base and local, deletion in remote
    b = [{'a': {'transient': 22}}]
    l = [{'a': {'transient': 242}}]
    b[0].update(common)
    l[0].update(common)
    r = []

    # Make decisions based on diffs with predicates
    ld = diff(b, l, path="", config=config)
    rd = diff(b, r, path="", config=config)

    # Assert that generic merge gives conflict
    strategies = Strategies()
    decisions = decide_merge_with_diff(b, l, r, ld, rd, strategies)
    assert apply_decisions(b, decisions) == b
    assert len(decisions) == 1
    assert decisions[0].conflict

    # Supply transient list to autoresolve, and check that transient is ignored
    strategies = Strategies(transients=[
        '/*/a/transient'
    ])
    decisions = decide_merge_with_diff(b, l, r, ld, rd, strategies)
    assert apply_decisions(b, decisions) == r
    assert not any(d.conflict for d in decisions)


def test_inline_merge_empty_notebooks():
    "Missing fields all around passes through."
    base = {}
    local = {}
    remote = {}
    expected = {}
    merged, decisions = merge_notebooks(base, local, remote)
    assert expected == merged


def test_inline_merge_dummy_notebooks():
    "Just the basic empty notebook passes through."
    base = new_notebook()
    local = new_notebook()
    remote = new_notebook()
    expected = new_notebook()
    merged, decisions = merge_notebooks(base, local, remote)
    assert expected == merged


def test_inline_merge_notebook_version():
    "Minor version gets bumped to max."
    base = new_notebook(nbformat=4, nbformat_minor=0)
    local = new_notebook(nbformat=4, nbformat_minor=1)
    remote = new_notebook(nbformat=4, nbformat_minor=2)
    expected = new_notebook(nbformat=4, nbformat_minor=2)
    merged, decisions = merge_notebooks(base, local, remote)
    assert expected == merged


def test_inline_merge_notebook_metadata(reset_log):
    """Merging a wide range of different value types
    and conflict types in the root /metadata dicts.
    The goal is to exercise a decent part of the
    generic diff and merge functionality.
    """

    untouched = {
        "string": "untouched string",
        "integer": 123,
        "float": 16.0,
        "list": ["hello", "world"],
        "dict": {"first": "Hello", "second": "World"},
    }
    md_in = {
        1: {
            "untouched": untouched,
            "unconflicted": {
                "int_deleteme": 7,
                "string_deleteme": "deleteme",
                "list_deleteme": [7, "deleteme"],
                "dict_deleteme": {"deleteme": "now", "removeme": True},
                "list_deleteitem": [7, "deleteme", 3, "notme", 5, "deletemetoo"],

                "string": "string v1",
                "integer": 456,
                "float": 32.0,
                "list": ["hello", "universe"],
                "dict": {"first": "Hello", "second": "World", "third": "!"},
            },
            "conflicted": {
                "int_delete_replace": 3,
                "string_delete_replace": "string that will be deleted and modified",
                "list_delete_replace": [1],
                "dict_delete_replace": {"k":"v"},

            #     "string": "string v1",
            #     "integer": 456,
            #     "float": 32.0,
            #     "list": ["hello", "universe"],
            #     "dict": {"first": "Hello", "second": "World"},
            }
        },
        2: {
            "untouched": untouched,
            "unconflicted": {
                "dict_deleteme": {"deleteme": "now", "removeme": True},
                "list_deleteitem": [7, 3, "notme", 5, "deletemetoo"],

                "string": "string v1 equal addition",
                "integer": 123, # equal change
                "float": 16.0, # equal change
                # Equal delete at beginning and insert of two values at end:
                "list": ["universe", "new items", "same\non\nboth\nsides"],
                # cases covered: twosided equal value change, onesided delete, onesided replace, onesided insert, twosided insert of same value
                "dict": {"first": "changed", "second": "World", "third": "!", "newkey": "newvalue", "otherkey": "othervalue"},
            },
            "conflicted": {
                "int_delete_replace": 5,
                "list_delete_replace": [2],

                # "string": "another text",
                 #"integer": 456,
            #     "float": 16.0,
            #     "list": ["hello", "world"],
            #     "dict": {"new": "value", "first": "Hello"}, #"second": "World"},

            #     "added_string": "another text",
            #     "added_integer": 9,
            #     "added_float": 16.0,
            #     "added_list": ["another", "multiverse"],
            #     "added_dict": {"1st": "hey", "2nd": "there"},
            }
        },
        3: {
            "untouched": untouched,
            "unconflicted": {
                "list_deleteme": [7, "deleteme"],
                "list_deleteitem": [7, "deleteme", 3, "notme", 5],

                "string": "string v1 equal addition",
                "integer": 123, # equal change
                "float": 16.0, # equal change
                # Equal delete at beginning and insert of two values at end:
                "list": ["universe", "new items", "same\non\nboth\nsides"],
                "dict": {"first": "changed", "third": ".", "newkey": "newvalue"},
            },
            "conflicted": {
                "string_delete_replace": "string that is modified here and deleted in the other version",
                "dict_delete_replace": {"k":"x","q":"r"},

            #     "string": "different message",
            #     "integer": 456,
            #     #"float": 16.0,
            #     "list": ["hello", "again", "world"],
            #     "dict": {"new": "but different", "first": "Hello"}, #"second": "World"},

            #     "added_string": "but not the same string",
            #     #"added_integer": 9,
            #     "added_float": 64.0,
            #     "added_list": ["initial", "values", "another", "multiverse", "trailing", "values"],
            #     "added_dict": {"3rt": "mergeme", "2nd": "conflict"},
            }
        }
    }

    def join_dicts(dicta, dictb):
        d = {}
        d.update(dicta)
        d.update(dictb)
        return d

    shared_unconflicted = {
        "list_deleteitem": [7, 3, "notme", 5],

        "string": "string v1 equal addition",
        "integer": 123,
        "float": 16.0,
        "list": ["universe", "new items", "same\non\nboth\nsides"],
        "dict": {"first": "changed", "third": ".",  "newkey": "newvalue", "otherkey": "othervalue"},
    }
    shared_conflicted = {
        "int_delete_replace": 3,
        "string_delete_replace": "string that will be deleted and modified",
        "list_delete_replace": [1],
        "dict_delete_replace": {"k":"v"},

    #     #"string": "string v1",
    #     "string": "another textdifferent message",

    #     "float": 32.0,
    #     "list": ["hello", "universe"],
    #     "dict": {"first": "Hello", "second": "World"},
    #     # FIXME
    }

    md_out = {
        (1,2,3): {
            "untouched": untouched,
            "unconflicted": join_dicts(shared_unconflicted, {
                # ...
            }),
            "conflicted": join_dicts(shared_conflicted, {
                # ...
            }),
        },
        (1,3,2): {
            "untouched": untouched,
            "unconflicted": join_dicts(shared_unconflicted, {
                # ...
            }),
            "conflicted": join_dicts(shared_conflicted, {
                # ...
            }),
        },
    }

    # Fill in expected conflict records
    for triplet in sorted(md_out.keys()):
        i, j, k = triplet
        local_diff = diff(md_in[i]["conflicted"], md_in[j]["conflicted"])
        remote_diff = diff(md_in[i]["conflicted"], md_in[k]["conflicted"])

        # This may not be a necessary test, just checking my expectations
        assert local_diff == sorted(local_diff, key=lambda x: x.key)
        assert remote_diff == sorted(remote_diff, key=lambda x: x.key)

        c = {
            # These are patches on the /metadata dict
            "local_diff": [op_patch("conflicted", local_diff)],
            "remote_diff": [op_patch("conflicted", remote_diff)],
        }
        md_out[triplet]["nbdime-conflicts"] = c

    # Fill in the trivial merge results
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            for k in (i, j):
                # For any combination i,j,i or i,j,j the
                # result should be j with no conflicts
                md_out[(i,j,k)] = md_in[j]

    tested = set()
    # Check the trivial merge results
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            for k in (i, j):
                triplet = (i, j, k)
                tested.add(triplet)
                base = new_notebook(metadata=md_in[i])
                local = new_notebook(metadata=md_in[j])
                remote = new_notebook(metadata=md_in[k])
                # For any combination i,j,i or i,j,j the result should be j
                expected = new_notebook(metadata=md_in[j])
                merged, decisions = merge_notebooks(base, local, remote)
                assert "nbdime-conflicts" not in merged["metadata"]
                assert not any([d.conflict for d in decisions])
                assert expected == merged

    # Check handcrafted merge results
    for triplet in sorted(md_out.keys()):
        i, j, k = triplet
        tested.add(triplet)
        base = new_notebook(metadata=md_in[i])
        local = new_notebook(metadata=md_in[j])
        remote = new_notebook(metadata=md_in[k])
        expected = new_notebook(metadata=md_out[triplet])
        merged, decisions = merge_notebooks(base, local, remote)
        if "nbdime-conflicts" in merged["metadata"]:
            assert any([d.conflict for d in decisions])
        else:
            assert not any([d.conflict for d in decisions])
        assert expected == merged

    # At least try to run merge without crashing for permutations
    # of md_in that we haven't constructed expected results for
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            for k in (1, 2, 3):
                triplet = (i, j, k)
                if triplet not in tested:
                    base = new_notebook(metadata=md_in[i])
                    local = new_notebook(metadata=md_in[j])
                    remote = new_notebook(metadata=md_in[k])
                    merged, decisions = merge_notebooks(base, local, remote)


def test_inline_merge_notebook_metadata_reproduce_bug(reset_log):
    md_in = {
        1: {
            "unconflicted": {
                "list_deleteitem": [7, "deleteme", 3, "notme", 5, "deletemetoo"],
            },
            "conflicted": {
                "dict_delete_replace": {"k":"v"},
            }
        },
        2: {
            "unconflicted": {
                "list_deleteitem": [7, 3, "notme", 5, "deletemetoo"],
            },
            "conflicted": {
            }
        },
        3: {
            "unconflicted": {
                "list_deleteitem": [7, "deleteme", 3, "notme", 5],
            },
            "conflicted": {
                "dict_delete_replace": {"k":"x"},
            }
        }
    }

    shared_unconflicted = {
        "list_deleteitem": [7, 3, "notme", 5],
    }
    shared_conflicted = {
        "dict_delete_replace": {"k":"v"},
    }

    md_out = {
        (1,2,3): {
            "unconflicted": shared_unconflicted,
            "conflicted": shared_conflicted
        },
    }

    # Fill in expected conflict records
    for triplet in sorted(md_out.keys()):
        i, j, k = triplet
        local_diff = diff(md_in[i]["conflicted"], md_in[j]["conflicted"])
        remote_diff = diff(md_in[i]["conflicted"], md_in[k]["conflicted"])

        # This may not be a necessary test, just checking my expectations
        assert local_diff == sorted(local_diff, key=lambda x: x.key)
        assert remote_diff == sorted(remote_diff, key=lambda x: x.key)

        c = {
            # These are patches on the /metadata dict
            "local_diff": [op_patch("conflicted", local_diff)],
            "remote_diff": [op_patch("conflicted", remote_diff)],
        }
        md_out[triplet]["nbdime-conflicts"] = c

    # Check handcrafted merge results
    triplet = (1,2,3)
    i, j, k = triplet
    base = new_notebook(metadata=md_in[i])
    local = new_notebook(metadata=md_in[j])
    remote = new_notebook(metadata=md_in[k])
    expected = new_notebook(metadata=md_out[triplet])
    merged, decisions = merge_notebooks(base, local, remote)
    if "nbdime-conflicts" in merged["metadata"]:
        assert any([d.conflict for d in decisions])
    else:
        assert not any([d.conflict for d in decisions])
    assert expected == merged


def test_inline_merge_source_empty():
    base = new_notebook()
    local = new_notebook()
    remote = new_notebook()
    expected = new_notebook()
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def code_nb(sources, strip_ids=False):
    nb = new_notebook(cells=[new_code_cell(s) for s in sources])
    strip_cell_ids(nb)
    return nb


def test_inline_merge_source_all_equal():
    base = code_nb([
        "first source",
        "other text",
        "yet more content",
    ])
    local = base
    remote = base
    expected = base
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def test_inline_merge_source_cell_deletions():
    "Cell deletions on both sides, onesided and agreed."
    base = code_nb([
        "first source",
        "other text",
        "yet more content",
        "and a final line",
        ])
    local = code_nb([
        #"first source",
        "other text",
        #"yet more content",
        #"and a final line",
        ])
    remote = code_nb([
        "first source",
        #"other text",
        "yet more content",
        #"and a final line",
        ])
    empty = code_nb([])
    for a in [base, local, remote, empty]:
        for b in [base, local, remote, empty]:
            merged, decisions = merge_notebooks(base, a, b)
            if a is b:
                assert merged == a
            elif a is base:
                assert merged == b
            elif b is base:
                assert merged == a
            else:
                # All other combinations will delete all cells
                assert merged == empty


def test_inline_merge_source_onesided_only():
    "A mix of changes on one side (delete, patch, remove)."
    base = code_nb([
        "first source",
        "other text",
        "yet more content",
        ])
    changed = code_nb([
        #"first source", # deleted
        "other text v2",
        "a different cell inserted",
        "yet more content",
        ])
    merged, decisions = merge_notebooks(base, changed, base)
    assert merged == changed
    merged, decisions = merge_notebooks(base, base, changed)
    assert merged == changed


def test_inline_merge_source_replace_line():
    "More elaborate test of cell deletions on both sides, onesided and agreed."
    # Note: Merge rendering of conflicted sources here will depend on git/diff/builtin params and availability
    base = code_nb([
        "first source",
        "other text",
        "this cell will be deleted and patched",
        "yet more content",
        "and a final line",
        ], strip_ids=True)
    local = code_nb([
        "1st source",  # onesided change
        "other text",
        #"this cell will be deleted and patched",
        "some more content",  # twosided equal change
        "And a Final line",  # twosided conflicted change
        ], strip_ids=True)
    remote = code_nb([
        "first source",
        "other text?",  # onesided change
        "this cell will be deleted and modified",
        "some more content",   # equal
        "and The final Line",  # conflicted
        ], strip_ids=True)
    expected = code_nb([
        "1st source",
        "other text?",
        #'<<<<<<< local <CELL DELETED>\n\n=======\nthis cell will be deleted and modified\n>>>>>>> remote'
        '<<<<<<< LOCAL CELL DELETED >>>>>>>\nthis cell will be deleted and modified',
        "some more content",  # equal
        '<<<<<<< local\nAnd a Final line\n=======\nand The final Line\n>>>>>>> remote'
        ], strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected
    expected = code_nb([
        "1st source",
        "other text?",
        #'<<<<<<< local\nthis cell will be deleted and modified\n=======\n>>>>>>> remote <CELL DELETED>'
        '<<<<<<< REMOTE CELL DELETED >>>>>>>\nthis cell will be deleted and modified',
        "some more content",
        '<<<<<<< local\nand The final Line\n=======\nAnd a Final line\n>>>>>>> remote'
        ], strip_ids=True)
    merged, decisions = merge_notebooks(base, remote, local)
    assert merged == expected


def test_inline_merge_source_add_to_line():
    "More elaborate test of cell deletions on both sides, onesided and agreed."
    # Note: Merge rendering of conflicted sources here will depend on git/diff/builtin params and availability
    base = code_nb([
        "first source",
        "other text",
        "this cell will be deleted and patched\nhere we add",
        "yet more content",
        "and a final line",
        ], strip_ids=True)
    local = code_nb([
        "1st source",  # onesided change
        "other text",
        #"this cell will be deleted and patched",
        "some more content",  # twosided equal change
        "And a Final line",  # twosided conflicted change
        ], strip_ids=True)
    remote = code_nb([
        "first source",
        "other text?",  # onesided change
        "this cell will be deleted and patched\nhere we add text to a line",
        "some more content",   # equal
        "and The final Line",  # conflicted
        ], strip_ids=True)
    expected = code_nb([
        "1st source",
        "other text?",
        #'<<<<<<< local <CELL DELETED>\n\n=======\nthis cell will be deleted and modified\n>>>>>>> remote'
        '<<<<<<< LOCAL CELL DELETED >>>>>>>\nthis cell will be deleted and patched\nhere we add text to a line',
        "some more content",  # equal
        '<<<<<<< local\nAnd a Final line\n=======\nand The final Line\n>>>>>>> remote'
        ], strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected
    expected = code_nb([
        "1st source",
        "other text?",
        #'<<<<<<< local\nthis cell will be deleted and modified\n=======\n>>>>>>> remote <CELL DELETED>'
        '<<<<<<< REMOTE CELL DELETED >>>>>>>\nthis cell will be deleted and patched\nhere we add text to a line',
        "some more content",
        '<<<<<<< local\nand The final Line\n=======\nAnd a Final line\n>>>>>>> remote'
        ], strip_ids=True)
    merged, decisions = merge_notebooks(base, remote, local)
    assert merged == expected


def test_inline_merge_source_patches_both_ends():
    "More elaborate test of cell deletions on both sides, onesided and agreed."
    # Note: Merge rendering of conflicted sources here will depend on git/diff/builtin params and availability
    base = code_nb([
        "first source will be modified",
        "other text",
        "this cell will be untouched",
        "yet more content",
        "and final line will be changed",
        ], strip_ids=True)
    local = code_nb([
        "first source will be modified locally",
        "other text",
        "this cell will be untouched",
        "yet more content",
        "and final line will be changed locally",
        ], strip_ids=True)
    remote = code_nb([
        "first source will be modified remotely",
        "other text",
        "this cell will be untouched",
        "yet more content",
        "and final line will be changed remotely",
        ], strip_ids=True)
    expected = code_nb([
        '<<<<<<< local\nfirst source will be modified locally\n=======\nfirst source will be modified remotely\n>>>>>>> remote',
        "other text",
        "this cell will be untouched",
        "yet more content",
        '<<<<<<< local\nand final line will be changed locally\n=======\nand final line will be changed remotely\n>>>>>>> remote',
        ], strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected
    expected = code_nb([
        '<<<<<<< local\nfirst source will be modified remotely\n=======\nfirst source will be modified locally\n>>>>>>> remote',
        "other text",
        "this cell will be untouched",
        "yet more content",
        '<<<<<<< local\nand final line will be changed remotely\n=======\nand final line will be changed locally\n>>>>>>> remote',
        ], strip_ids=True)
    merged, decisions = merge_notebooks(base, remote, local)
    assert merged == expected


def test_inline_merge_source_patch_delete_conflicts_both_ends():
    "More elaborate test of cell deletions on both sides, onesided and agreed."
    # Note: Merge rendering of conflicted sources here will depend on git/diff/builtin params and availability
    base = code_nb([
        "first source will be modified",
        "other text",
        "this cell will be untouched",
        "yet more content",
        "and final line will be changed",
        ])
    local = code_nb([
        "first source will be modified on one side",
        "other text",
        "this cell will be untouched",
        "yet more content",
        #"and final line will be deleted locally",
        ])
    remote = code_nb([
        #"first source will be deleted remotely",
        "other text",
        "this cell will be untouched",
        "yet more content",
        "and final line will be changed on one side",
        ])
    expected = code_nb([
        '<<<<<<< REMOTE CELL DELETED >>>>>>>\nfirst source will be modified on one side',
        "other text",
        "this cell will be untouched",
        "yet more content",
        '<<<<<<< LOCAL CELL DELETED >>>>>>>\nand final line will be changed on one side',
        ])
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected
    expected = code_nb([
        '<<<<<<< LOCAL CELL DELETED >>>>>>>\nfirst source will be modified on one side',
        "other text",
        "this cell will be untouched",
        "yet more content",
        '<<<<<<< REMOTE CELL DELETED >>>>>>>\nand final line will be changed on one side',
        ])
    merged, decisions = merge_notebooks(base, remote, local)
    assert merged == expected


def test_inline_merge_attachments():
    # FIXME: Use output creation utils Vidar wrote in another test file
    base = new_notebook()
    local = new_notebook()
    remote = new_notebook()
    expected = new_notebook()
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def test_inline_merge_outputs():
    # One cell with two outputs:
    base = outputs_to_notebook([['unmodified', 'base']], strip_ids=True)
    local = outputs_to_notebook([['unmodified', 'local']], strip_ids=True)
    remote = outputs_to_notebook([['unmodified', 'remote']], strip_ids=True)
    expected = outputs_to_notebook([[
        'unmodified',
        nbformat.v4.new_output(
            output_type='stream', name='stderr',
            text='<<<<<<< local <modified: text/plain>\n'),
        'local',
        nbformat.v4.new_output(
            output_type='stream', name='stderr',
            text='=======\n'),
        'remote',
        nbformat.v4.new_output(
            output_type='stream', name='stderr',
            text='>>>>>>> remote <modified: text/plain>\n'),
    ]], strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def test_inline_merge_outputs_conflicting_insert_in_empty():
    # One cell with two outputs:
    base = outputs_to_notebook([[]], strip_ids=True)
    local = outputs_to_notebook([['local']], strip_ids=True)
    remote = outputs_to_notebook([['remote']], strip_ids=True)
    expected = outputs_to_notebook([[
        nbformat.v4.new_output(
            output_type='stream', name='stderr',
            text='<<<<<<< local\n'),
        'local',
        nbformat.v4.new_output(
            output_type='stream', name='stderr',
            text='=======\n'),
        'remote',
        nbformat.v4.new_output(
            output_type='stream', name='stderr',
            text='>>>>>>> remote\n'),
    ]], strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def test_inline_merge_cells_insertion_similar():
    base = sources_to_notebook([['unmodified']], cell_type='markdown', strip_ids=True)
    local = sources_to_notebook([['unmodified'], ['local']], cell_type='markdown', strip_ids=True)
    remote = sources_to_notebook([['unmodified'], ['remote']], cell_type='markdown', strip_ids=True)
    expected = sources_to_notebook([
        'unmodified',
        [
            ("<"*7) + ' local\n',
            'local\n',
            ("="*7) + '\n',
            'remote\n',
            (">"*7) + ' remote'
        ]
    ], cell_type='markdown', strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def test_inline_merge_cells_insertion_unsimilar():
    base = sources_to_notebook([['unmodified']], cell_type='markdown', strip_ids=True)
    local = sources_to_notebook([['unmodified'], ['local\n', 'friendly faces\n', '3.14']], cell_type='markdown', strip_ids=True)
    remote = sources_to_notebook([['unmodified'], ['remote\n', 'foo bar baz\n']], cell_type='markdown', strip_ids=True)
    expected = sources_to_notebook([
        ['unmodified'],
        [_cell_marker_format(("<"*7) + ' local')],
        ['local\n', 'friendly faces\n', '3.14'],
        [_cell_marker_format("="*7)],
        ['remote\n', 'foo bar baz\n'],
        [_cell_marker_format((">"*7) + ' remote')],
    ], cell_type='markdown', strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert strip_cell_ids(merged) == expected


def test_inline_merge_cells_replacement_similar():
    base = sources_to_notebook([['unmodified'], ['base']], cell_type='markdown', strip_ids=False)
    local = sources_to_notebook([['unmodified'], ['local']], cell_type='markdown', strip_ids=True)
    remote = sources_to_notebook([['unmodified'], ['remote']], cell_type='markdown', strip_ids=True)
    expected = sources_to_notebook([
        ['unmodified'],
        [
            ("<"*7) + ' local\n',
            'local\n',
            ("="*7) + '\n',
            'remote\n',
            (">"*7) + ' remote'
        ]
    ], cell_type='markdown', strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert merged == expected


def test_inline_merge_cells_replacement_unsimilar():
    base = sources_to_notebook([['unmodified'], ['base']], cell_type='markdown', strip_ids=False)
    local = sources_to_notebook([['unmodified'], ['local\n', 'friendly faces\n', '3.14']], cell_type='markdown', strip_ids=True)
    remote = sources_to_notebook([['unmodified'], ['remote\n', 'foo bar baz\n']], cell_type='markdown', strip_ids=True)
    expected = sources_to_notebook([
        ['unmodified'],
        [_cell_marker_format(("<"*7) + ' local')],
        ['local\n', 'friendly faces\n', '3.14'],
        [_cell_marker_format("="*7)],
        ['remote\n', 'foo bar baz\n'],
        [_cell_marker_format((">"*7) + ' remote')],
    ], cell_type='markdown', strip_ids=True)
    merged, decisions = merge_notebooks(base, local, remote)
    assert strip_cell_ids(merged) == expected
