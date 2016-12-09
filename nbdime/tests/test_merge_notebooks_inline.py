

import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell, new_output

from nbdime import merge_notebooks, diff
from nbdime.diff_format import op_patch


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


def test_inline_merge_notebook_metadata():
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
                for d in decisions:
                    assert not d.conflict 
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
        for d in decisions:
            assert not d.conflict 
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
