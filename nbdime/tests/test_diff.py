# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import pytest
import copy

from nbdime import patch, shallow_diff, deep_diff

from .fixtures import check_diff_and_patch, check_symmetric_diff_and_patch

def test_diff_and_patch():
    # Note: check_symmetric_diff_and_patch handles (a,b) and (b,a) for both
    # shallow and deep diffs, simplifying the number of cases to cover in here.

    # Empty
    mda = {}
    mdb = {}
    check_symmetric_diff_and_patch(mda, mdb)

    # One-sided content/empty
    mda = {"a": 1}
    mdb = {}
    check_symmetric_diff_and_patch(mda, mdb)

    # One-sided content/empty multilevel
    mda = {"a": 1, "b": {"ba": 21}}
    mdb = {}
    check_symmetric_diff_and_patch(mda, mdb)

    # One-sided content/empty multilevel
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {}
    check_symmetric_diff_and_patch(mda, mdb)

    # Partial delete
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31}}
    check_symmetric_diff_and_patch(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    check_symmetric_diff_and_patch(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"b": {"ba": 21}, "c": {"cb": 32}}
    check_symmetric_diff_and_patch(mda, mdb)

    # One-level modification
    mda = {"a": 1}
    mdb = {"a": 10}
    check_symmetric_diff_and_patch(mda, mdb)

    # Two-level modification
    mda = {"a": 1, "b": {"ba": 21}}
    mdb = {"a": 10, "b": {"ba": 210}}
    check_symmetric_diff_and_patch(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}}
    mdb = {"a": 1, "b": {"ba": 210}}
    check_symmetric_diff_and_patch(mda, mdb)

    # Multilevel modification
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"a": 10, "b": {"ba": 210}, "c": {"ca": 310, "cb": 320}}
    check_symmetric_diff_and_patch(mda, mdb)
    mda = {"a": 1, "b": {"ba": 21}, "c": {"ca": 31, "cb": 32}}
    mdb = {"a": 1, "b": {"ba": 210}, "c": {"ca": 310, "cb": 32}}
    check_symmetric_diff_and_patch(mda, mdb)

    # Multilevel mix of delete, add, modify
    mda = {"deleted": 1, "modparent": {"mod": 21}, "mix": {"del": 31, "mod": 32, "unchanged": 123}}
    mdb = {"added": 7,   "modparent": {"mod": 22}, "mix": {"add": 42, "mod": 37, "unchanged": 123}}
    check_symmetric_diff_and_patch(mda, mdb)
    # A more explicit assert showing the diff format and testing that paths are sorted:
    assert shallow_diff(mda, mdb) == [
        ['-', 'deleted'],
        [':', 'mix', {"add": 42, "mod": 37, "unchanged": 123}],
        [':', 'modparent', {"mod": 22}],
        ['+', 'added', 7],
        ]
    assert deep_diff(mda, mdb) == [
        ['-', 'deleted'],
        ['!', 'mix', [
            ['-', 'del'],
            [':', 'mod', 37],
            ['+', 'add', 42]
            ]],
        ['!', 'modparent', [
            [':', 'mod', 22]
            ]],
        ['+', 'added', 7],
        ]
