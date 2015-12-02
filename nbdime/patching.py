# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from six import string_types
import copy
import nbformat

from .dformat import error_invalid_diff_entry


__all__ = ["patch", "patch_notebook"]


def patch_list(obj, diff):
    # The patched sequence to build and return
    newobj = []
    # Index into obj, the next item to take unless diff says otherwise
    take = 0
    for s in diff:
        action = s[0]
        index = s[1]
        assert isinstance(index, int)

        # Take values from obj not mentioned in diff, up to not including index
        newobj.extend(copy.deepcopy(value) for value in obj[take:index])

        if action == "+":
            # Append new value directly
            newobj.append(s[2])
            skip = 0
        elif action == "-":
            # Delete values obj[index] by incrementing take to skip
            skip = 1
        elif action == ":":
            # Replace value at obj[index] with s[2]
            newobj.append(s[2])
            skip = 1
        elif action == "!":
            # Patch value at obj[index] with diff s[2]
            newobj.append(patch(obj[index], s[2]))
            skip = 1
        # Experimental sequence diff actions:
        elif action == "++":
            # Extend with new values directly
            newobj.extend(s[2])
            skip = 0
        elif action == "--":
            # Delete values obj[index:index+s[2]] by incrementing take to skip
            skip = s[2]
        elif action == "::":
            # Replace values at obj[index:index+len(s[2])] with s[2]
            newobj.extend(s[2])
            skip = len(s[2])
        else:
            error_invalid_diff_entry(s)

        # Skip the specified number of elements, but never decrement take.
        # Note that take can pass index in diffs with repeated +/- on the
        # same index, i.e. [["-", index], ["+", index, value]]
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
    for s in diff:
        action = s[0]
        key = s[1]
        assert isinstance(key, string_types)

        if action == "+":
            assert key not in keys_to_copy
            newobj[key] = s[2]
        elif action == "-":
            keys_to_copy.remove(key)
        elif action == ":":
            keys_to_copy.remove(key)
            newobj[key] = s[2]
        elif action == "!":
            keys_to_copy.remove(key)
            newobj[key] = patch(obj[key], s[2])
        else:
            error_invalid_diff_entry(s)
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
