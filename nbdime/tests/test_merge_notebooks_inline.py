

import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell, new_output

from nbdime import merge_notebooks


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

    unconflicted = {
        "string": "unconflicted string",
        "integer": 123,
        "float": 16.0,
        "list": ["hello", "world"],
        "dict": {"first": "Hello", "second": "World"},
    }
    md_in = {
        1: {
            "unconflicted": unconflicted,
            "conflicted": {
                "string": "string v1",
                "integer": 456,
                "float": 32.0,
                "list": ["hello", "universe"],
                "dict": {"first": "Hello", "second": "World"},
            }
        },
        2: {
            "unconflicted": unconflicted,
            "conflicted": {
                "string": "another text",
                #"integer": 123,
                "float": 16.0,
                "list": ["hello", "world"],
                "dict": {"new": "value", "first": "Hello"}, #"second": "World"},

                "added_string": "another text",
                "added_integer": 9,
                "added_float": 16.0,
                "added_list": ["another", "multiverse"],
                "added_dict": {"1st": "hey", "2nd": "there"},
            }
        },
        3: {
            "unconflicted": unconflicted,
            "conflicted": {
                "string": "different message",
                #"i1nteger": 123,
                #"float": 16.0,
                "list": ["hello", "again", "world"],
                "dict": {"new": "but different", "first": "Hello"}, #"second": "World"},

                "added_string": "but not the same string",
                #"added_integer": 9,
                "added_float": 64.0,
                "added_list": ["initial", "values", "another", "multiverse", "trailing", "values"],
                "added_dict": {"3rt": "mergeme", "2nd": "conflict"},
            }
        }
    }
    md_out = {
        (1,2,3): {
            "unconflicted": unconflicted,
            "conflicted": {
                # FIXME
            }
        },
        (1,3,2): {
            "unconflicted": unconflicted,
            "conflicted": {
                # FIXME
            }
        },
        (2,1,3): {
            "unconflicted": unconflicted,
            "conflicted": {
                # FIXME
            }
        },
        (2,3,1): {
            "unconflicted": unconflicted,
            "conflicted": {
                # FIXME
            }
        },
        (3,1,2): {
            "unconflicted": unconflicted,
            "conflicted": {
                # FIXME
            }
        },
        (3,2,1): {
            "unconflicted": unconflicted,
            "conflicted": {
                # FIXME
            }
        }
    }

    # Fill in the trivial merge results
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            for k in (i, j):
                # For any combination i,j,i or i,j,j the result should be j
                md_out[(i,j,k)] = md_in[j]

    # Check the trivial merge results
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            for k in (i, j):
                base = new_notebook(metadata=md_in[i])
                local = new_notebook(metadata=md_in[j])
                remote = new_notebook(metadata=md_in[k])
                # For any combination i,j,i or i,j,j the result should be j
                expected = new_notebook(metadata=md_in[j])
                merged, decisions = merge_notebooks(base, local, remote)
                assert expected == merged

    # Check handcrafted merge results
    for triplet in sorted(md_out.keys()):
        i, j, k = triplet
        base = new_notebook(metadata=md_in[i])
        local = new_notebook(metadata=md_in[j])
        remote = new_notebook(metadata=md_in[k])
        expected = new_notebook(metadata=md_out[triplet])
        merged, decisions = merge_notebooks(base, local, remote)
        #assert expected == merged  # FIXME: Enable when expected values are filled in
