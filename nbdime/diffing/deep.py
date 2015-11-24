# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import operator

from ..dformat import validate_diff, count_consumed_symbols
from .sequences import diff_strings, diff_sequence

# TODO: These should probably be more customizable
from .comparing import is_atomic, is_similar

__all__ = ["deep_diff", "deep_diff_lists", "deep_diff_dicts"]


def deep_diff_lists(a, b, compare=operator.__eq__):
    # First make the one-level list diff with custom compare
    di = diff_sequence(a, b, compare)

    # Count consumed items from a, 'take' in patch_list
    acons = 0
    bcons = 0
    pdi = []
    for e in di:
        action = e[0]
        index = e[1]

        # Consume n more unmentioned items.
        # Note that index can be larger than acons in the case where items
        # have been deleted from a and then insertions from b occur.
        n = max(0, index - acons)
        for i in range(n):
            aval = a[acons+i]
            bval = b[bcons+i]
            # If we get here, this should hold: (FIXME: remove later, could be expensive)
            assert compare(aval, bval) == True
            # Recursively deep_diff the items that have been deemed similar
            if not is_atomic(aval):
                d = deep_diff(aval, bval, compare)
                if d:
                    pdi.append(["!", acons+i, d])

        # Count consumed items
        askip, bskip = count_consumed_symbols(e)
        acons += n + askip
        bcons += n + bskip

        # Now insert the diff entry
        pdi.append(e)

    # Consume final items
    n = len(a) - acons
    assert n >= 0
    assert len(b) - bcons == n
    for i in range(n): # TODO: Get rid of code duplication
        aval = a[acons+i]
        bval = b[bcons+i]
        # If we get here, this should hold: (FIXME: remove later, could be expensive)
        assert compare(aval, bval) == True
        # Recursively deep_diff the non-atomic items that have been deemed similar
        if not is_atomic(aval):
            d = deep_diff(aval, bval, compare)
            if d:
                pdi.append(["!", acons+i, d])

    # Sanity check
    acons += n
    bcons += n
    assert acons == len(a)
    assert bcons == len(b)

    return pdi


def deep_diff_dicts(a, b, compare=operator.__eq__):
    """Compute diff of two dicts with configurable behaviour.

    Keys in both a and b will be handled based on

    Make a one-level diff of dicts a and b, using given compare
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
        # If types are the same and nonatomic, recurse
        if type(avalue) == type(bvalue) and not is_atomic(avalue):
            dd = deep_diff(avalue, bvalue, compare)
            if dd:
                # Patch value at key with nonzero diff dd
                d.append(['!', key, dd])
        else:
            if not compare(avalue, bvalue): # TODO: Use != or not compare() here?
                # Replace value at key with bvalue
                d.append([':', key, bvalue])

    # Add keys in b but not in a
    for key in sorted(bkeys - akeys):
        d.append(['+', key, b[key]])

    return d


def deep_diff(a, b, compare=operator.__eq__):
    "Compute the diff of two json-like objects, list or dict or string."

    # TODO: Providing separate comparison predicate for
    # different dict paths will allow more customization

    if isinstance(a, list) and isinstance(b, list):
        d = deep_diff_lists(a, b, compare)
    elif isinstance(a, dict) and isinstance(b, dict):
        d = deep_diff_dicts(a, b, compare)
    elif isinstance(a, basestring) and isinstance(b, basestring):
        d = diff_strings(a, b)
    else:
        raise RuntimeError("Can currently only diff list, dict, or str objects.")

    # We can turn this off for performance after the library has been well tested:
    validate_diff(d)

    return d
