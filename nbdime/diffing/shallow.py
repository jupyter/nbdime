# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import operator
from six import string_types

from ..dformat import validate_diff
from .sequences import diff_sequence, diff_strings
from .seq_difflib import diff_sequence_difflib

__all__ = ["shallow_diff", "shallow_diff_lists", "shallow_diff_dicts"]


# Using this sentinel instead of None in dict.get calls to allow the value None
Missing = object()


def shallow_diff_lists(a, b, compare):
    """Equality-based diff of two lists.

    Will probably be replaced with some of the more flexible tools.
    """
    assert isinstance(a, list) and isinstance(b, list)
    return diff_sequence(a, b, compare)


def old_shallow_diff_dicts(a, b, compare=operator.__eq__):
    """Make a one-level diff of dicts a and b, using given compare
    operator to specify which items are considered the same.

    Items not mentioned in diff are items where compare(x, y) return True.
    For other items the diff will contain delete, insert, or replace entries.
    """
    assert isinstance(a, dict) and isinstance(b, dict)
    d = []
    # Sort keys to get a deterministic diff result
    for key in sorted(a.keys()):
        bvalue = b.get(key, Missing)
        if bvalue is Missing:
            # key is not in b, deleting avalue
            d.append(['-', key])
        else:
            avalue = a[key]
            # key is in both a and b
            if not compare(avalue, bvalue):
                # values are different, so we replace old with new
                d.append([':', key, bvalue])
    for key in sorted(b.keys()):
        bvalue = b[key]
        avalue = a.get(key, Missing)
        if avalue is Missing:
            # key is not in a, adding bvalue
            d.append(['+', key, bvalue])
    return d


def shallow_diff_dicts(a, b, compare=operator.__eq__):
    """Make a one-level diff of dicts a and b, using given compare
    operator to specify which items are considered the same.

    Items not mentioned in diff are items where compare(x, y) return True.
    For other items the diff will contain delete, insert, or replace entries.
    """
    assert isinstance(a, dict) and isinstance(b, dict)
    d = []

    # Sorting keys in loops to get a deterministic diff result
    akeys = set(a.keys())
    bkeys = set(b.keys())

    # Delete keys in a but not in b
    for key in sorted(akeys - bkeys):
        d.append(['-', key])

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]
        if not compare(avalue, bvalue):
            # Replace value at key with bvalue
            d.append([':', key, bvalue])

    # Add keys in b but not in a
    for key in sorted(bkeys - akeys):
        d.append(['+', key, b[key]])

    return d


def alternative_shallow_diff_dicts(a, b, compare=operator.__eq__):
    """Make a one-level diff of dicts a and b, using given compare
    operator to specify which items are considered the same.

    Items not mentioned in diff are items where compare(x, y) return True.
    For other items the diff will contain delete, insert, or replace entries.
    """
    assert isinstance(a, dict) and isinstance(b, dict)
    d = {}

    # Sorting keys in loops to get a deterministic diff result
    akeys = set(a.keys())
    bkeys = set(b.keys())

    # Delete keys in a but not in b
    for key in akeys - bkeys:
        d[key] = ["-"]

    # Handle values for keys in both a and b
    for key in akeys & bkeys:
        avalue = a[key]
        bvalue = b[key]
        if not compare(avalue, bvalue):
            # Replace value at key with bvalue
            d[key] = [":", bvalue]

    # Add keys in b but not in a
    for key in bkeys - akeys:
        d[key] = ["+", b[key]]

    return d


def shallow_diff(a, b, compare=operator.__eq__):
    """Compute the diff of two json-like objects, list or dict or string.

    Currently doesn't deal well with deeply nested structures and will
    be replaced with a better algorithm.
    """
    if isinstance(a, list) and isinstance(b, list):
        d = shallow_diff_lists(a, b, compare)
    elif isinstance(a, dict) and isinstance(b, dict):
        d = shallow_diff_dicts(a, b, compare)
    elif isinstance(a, string_types) and isinstance(b, string_types):
        d = diff_strings(a, b)
    else:
        raise RuntimeError("Can currently only diff list, dict, or str objects.")

    # We can turn this off for performance after the library has been well tested:
    validate_diff(d)

    return d
