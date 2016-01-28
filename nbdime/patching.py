# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
import copy
import nbformat

from .dformat import NBDiffFormatError
from .dformat import PATCH, ADD, DELETE, REPLACE, ADDRANGE, REMOVERANGE


__all__ = ["patch", "patch_notebook"]


def patch_list(obj, diff):
    # The patched sequence to build and return
    newobj = []
    # Index into obj, the next item to take unless diff says otherwise
    take = 0
    for e in diff:
        op = e.op
        index = e.key
        assert isinstance(index, int)

        # Take values from obj not mentioned in diff, up to not including index
        newobj.extend(copy.deepcopy(value) for value in obj[take:index])

        if op == ADD:
            # Append new value directly
            newobj.append(e.value)
            skip = 0
        elif op == DELETE:
            # Delete values obj[index] by incrementing take to skip
            skip = 1
        elif op == REPLACE:
            # Add replacement value and skip old
            newobj.append(e.value)
            skip = 1
        elif op == PATCH:
            newobj.append(patch(obj[index], e.diff))
            skip = 1
        elif op == ADDRANGE:
            # Extend with new values directly
            newobj.extend(e.values)
            skip = 0
        elif op == REMOVERANGE:
            # Delete a number of values by skipping
            skip = e.length
        else:
            raise NBDiffFormatError("Invalid op {}.".format(op))

        # Skip the specified number of elements, but never decrement take.
        # Note that take can pass index in diffs with repeated +/- on the
        # same index, i.e. [make_op(DELETE, index), make_op(ADD, index, value)]
        take = max(take, index + skip)

    # Take values at end not mentioned in diff
    newobj.extend(copy.deepcopy(value) for value in obj[take:len(obj)])

    return newobj


def patch_string(obj, diff):
    # This can possibly be optimized for str if wanted, but
    # waiting until patch_list has been tested and debugged better
    return "".join(patch_list(list(obj), diff))


def patch_dict(obj, diff):
    newobj = {}
    keys_to_copy = set(obj.keys())

    for e in diff:
        op = e.op
        key = e.key
        assert isinstance(key, string_types)

        if op == ADD:
            assert key not in keys_to_copy
            newobj[key] = e.value
        elif op == DELETE:
            keys_to_copy.remove(key)
        elif op == REPLACE:
            keys_to_copy.remove(key)
            newobj[key] = e.value
        elif op == PATCH:
            keys_to_copy.remove(key)
            newobj[key] = patch(obj[key], e.diff)
        else:
            raise NBDiffFormatError("Invalid op {}.".format(op))

    # Take items not mentioned in diff
    for key in keys_to_copy:
        newobj[key] = copy.deepcopy(obj[key])
    return newobj


def patch(obj, diff):
    """Produce a patched version of obj with given hierarchial diff.

    A valid input object can be any dict or list of leaf values,
    or arbitrarily nested dict or list of valid input objects.

    Dicts are required to have string keys.

    Leaf values are any non-dict, non-list objects as far as patch
    is concerned, although the intentional use of this library
    is that values are json-serializable.
    """
    if isinstance(obj, dict):
        return patch_dict(obj, diff)
    elif isinstance(obj, list):
        return patch_list(obj, diff)
    elif isinstance(obj, string_types):
        return patch_string(obj, diff)


def patch_notebook(nb, diff):
    return nbformat.from_dict(patch(nb, diff))
