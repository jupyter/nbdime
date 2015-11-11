from __future__ import print_function
import pytest
import copy
from nbmerge.diff.diff_metadata import diff_metadata, patch_metadata

from .fixtures import *

def check_diff_patch_metadata(a, b):
    "Check diff/patch of metadata symmetrically."
    assert patch_metadata(a, diff_metadata(a, b)) == b
    assert patch_metadata(b, diff_metadata(b, a)) == a

def test_diff_and_patch_metadata():
    # Note: check_diff_patch_metadata is symmetric, simplifying the number of cases to cover in here

    # Empty
    mda = {}
    mdb = {}
    check_diff_patch_metadata(mda, mdb)

    # One-sided content/empty
    mda = {"a": 1}
    mdb = {}
    check_diff_patch_metadata(mda, mdb)

    # One-sided content/empty multilevel
    mda = {"a": 1, "b": {"ba": 21}}
    mdb = {}
    check_diff_patch_metadata(mda, mdb)

    # One-sided content/empty multilevel
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {}
    check_diff_patch_metadata(mda, mdb)

    # Partial delete
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31}}
    check_diff_patch_metadata(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    check_diff_patch_metadata(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"b": {"ba": 21}, "c": {"cb": 32}}
    check_diff_patch_metadata(mda, mdb)

    # One-level modification
    mda = {"a": 1}
    mdb = {"a": 10}
    check_diff_patch_metadata(mda, mdb)

    # Two-level modification
    mda = {"a": 1, "b": {"ba": 21}}
    mdb = {"a": 10, "b": {"ba": 210}}
    check_diff_patch_metadata(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}}
    mdb = {"a": 1, "b": {"ba": 210}}
    check_diff_patch_metadata(mda, mdb)

    # Multilevel modification
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"a": 10, "b": {"ba": 210}, "c": {"ca": 310, "cb": 320}}
    check_diff_patch_metadata(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"a": 1, "b": {"ba": 210}, "c": {"ca": 310, "cb": 32}}
    check_diff_patch_metadata(mda, mdb)

    # Multilevel mix of delete, add, modify
    mda = {"deleted": 1, "modparent": {"mod": 21}, "mix": {"del": 31, "mod": 32, "unchanged": 123}}
    mdb = {"added": 7,   "modparent": {"mod": 22}, "mix": {"add": 42, "mod": 37, "unchanged": 123}}
    check_diff_patch_metadata(mda, mdb)
    # A more explicit assert showing the diff format and testing that paths are sorted:
    assert diff_metadata(mda, mdb) == [
        ['-', ['deleted']],
        ['-', ['mix', 'del']],
        ['!', ['mix', 'mod'], 37],
        ['!', ['mix', 'unchanged'], 123],
        ['+', ['mix', 'add'], 42],
        ['!', ['modparent', 'mod'], 22],
        ['+', ['added'], 7],
        ]
