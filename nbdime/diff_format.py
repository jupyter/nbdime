# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range
from collections import namedtuple

from .log import NBDiffFormatError


class DiffEntry(dict):
    def __getattr__(self, name):
        return self[name]
    def __setattr__(self, name, value):
        self[name] = value


def make_op(op, *args):
    """Create a diff entry with compact notation and error checking.

    Args depend on the op:

        * op = "add",         args = (key, value)
        * op = "remove",      args = (key,)
        * op = "replace",     args = (key, value)
        * op = "patch",       args = (key, diff)
        * op = "addrange",    args = (key, valuelist)
        * op = "removerange", args = (key, length)

    """
    if op == "addrange":
        key, valuelist = args
        return DiffEntry(op=op, key=key, valuelist=valuelist)
    elif op == "removerange":
        key, length = args
        return DiffEntry(op=op, key=key, length=length)
    elif op in ("add", "replace"):
        key, value = args
        return DiffEntry(op=op, key=key, value=value)
    elif op == "remove":
        key, = args
        return DiffEntry(op=op, key=key)
    elif op == "patch":
        key, diff = args
        return DiffEntry(op=op, key=key, diff=diff)
    else:
        raise NBDiffFormatError("Invalid op {}.".format(op))


class Diff(object):

    # Valid values for the action field in diff entries
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    ADDRANGE = "addrange"
    REMOVERANGE = "removerange"
    PATCH = "patch"


class SequenceDiff(Diff):

    # Valid values for the action field in sequence diff entries
    OPS = (
        Diff.ADDRANGE,
        Diff.REMOVERANGE,
        Diff.PATCH,
        )

    def __init__(self):
        self.diff = []

    def __len__(self):
        return len(self.diff)

    def __iter__(self):
        return iter(self.diff)

    def __getitem__(self, i):
        return self.diff[i]

    def append(self, entry):
        assert isinstance(entry, DiffEntry)
        self.diff.append(entry)

    def add(self, key, valuelist):
        self.append(make_op(Diff.ADDRANGE, key, valuelist))

    def remove(self, key, length):
        self.append(make_op(Diff.REMOVERANGE, key, length))

    def patch(self, key, diff):
        self.append(make_op(Diff.PATCH, key, diff))


class MappingDiff(Diff):

    # Valid values for the action field in mapping diff entries
    OPS = (
        Diff.ADD,
        Diff.REMOVE,
        Diff.REPLACE,
        Diff.PATCH,
        )

    def __init__(self):
        self.diff = []
        #self.diff = {}

    def __len__(self):
        return len(self.diff)

    def __iter__(self):
        return iter(self.diff)
        #return iter(self.diff.values())

    def append(self, entry):
        assert isinstance(entry, DiffEntry)
        self.diff.append(entry)
        #self.diff[entry.key] = entry

    def add(self, key, value):
        self.append(make_op(Diff.ADD, key, value))

    def remove(self, key):
        self.append(make_op(Diff.REMOVE, key))

    def replace(self, key, value):
        self.append(make_op(Diff.REPLACE, key, value))

    def patch(self, key, diff):
        self.append(make_op(Diff.PATCH, key, diff))


def is_valid_diff(diff, deep=False):
    try:
        validate_diff(diff, deep=deep)
        result = True
    except NBDiffFormatError:
        result = False
        raise
    return result


def validate_diff(diff, deep=False):
    if not isinstance(diff, list):
        raise NBDiffFormatError("Diff must be a list.")
    for e in diff:
        validate_diff_entry(e, deep=deep)


sequence_types = string_types + (list,)


def validate_diff_entry(e, deep=False):
    """Check that e is a well formed diff entry, as documented under docs/."""

    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(e, DiffEntry):
        raise NBDiffFormatError("Diff entry '{}' is not a diff type.".format(e))

    # Check key (list or str uses int key, dict uses str key)
    op = e.op
    key = e.key
    if isinstance(key, int) and op in SequenceDiff.OPS:
        if op == Diff.ADDRANGE:
            if not isinstance(e.valuelist, sequence_types):
                raise NBDiffFormatError("addrange expects a sequence of values to insert, not '{}'.".format(e.valuelist))
        elif op == Diff.REMOVERANGE:
            if not isinstance(e.length, int):
                raise NBDiffFormatError("removerange expects a number of values to delete, not '{}'.".format(e.length))
        elif op == Diff.PATCH:
            # e.diff is itself a diff, check it recursively if the "deep" argument is true
            # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
            if deep:
                validate_diff(e.diff, deep=deep)
        else:
            raise NBDiffFormatError("Unknown diff op '{}'.".format(op))
    elif isinstance(key, string_types) and op in MappingDiff.OPS:
        if op == Diff.ADD:
            pass  # e.value is a single value to insert at key
        elif op == Diff.REMOVE:
            pass  # no argument
        elif op == Diff.REPLACE:
            # e.value is a single value to replace value at key with
            pass
        elif op == Diff.PATCH:
            # e.diff is itself a diff, check it recursively if the "deep" argument is true
            # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
            if deep:
                validate_diff(e.diff, deep=deep)
        else:
            raise NBDiffFormatError("Unknown diff op '{}'.".format(op))
    else:
        msg = "Invalid diff entry key '{}' of type '{}'. Expecting int for sequences or unicode/str for mappings."
        raise NBDiffFormatError(msg.format(key, type(key)))

    # Note that false positives are possible, for example
    # we're not checking the values in any way, as they
    # can in principle be arbitrary json objects


def count_consumed_symbols(e):
    "Count how many symbols are consumed from each sequence by a single sequence diff entry."
    op = e.op
    if op == Diff.ADDRANGE:
        return (0, len(e.valuelist))
    elif op == Diff.REMOVERANGE:
        return (e.length, 0)
    elif op == Diff.PATCH:
        return (1, 1)
    else:
        raise NBDiffFormatError("Invalid op '{}'".format(op))


def source_as_string(source):
    "Return source as a single string, joined as lines if it's a list."
    if isinstance(source, list):
        source = "\n".join(line.strip("\n") for line in source)
    assert isinstance(source, string_types)
    return source


def to_clean_dicts(di):
    "Recursively convert dict-like objects to straight python dicts."
    if isinstance(di, dict):
        return {k: to_clean_dicts(v) for k, v in di.items()}
    elif isinstance(di, list):
        return [to_clean_dicts(v) for v in di]
    else:
        return di


def to_diffentry_dicts(di):  # TODO: Better name, validate_diff? as_diff?
    "Recursively convert dict objects to DiffEntry objects with attribute access."
    if isinstance(di, dict):
        return DiffEntry(**{k: to_diffentry_dicts(v) for k, v in di.items()})
    elif isinstance(di, list):
        return [to_diffentry_dicts(v) for v in di]
    else:
        return di


def to_json_patch(d, path=""):
    """Convert nbdime diff object into the RFC6902 JSON Patch format.

    This is untested and will need some details worked out.
    """
    jp = []
    for e in d:
        op = e.op
        p = "/".join([path, str(e.key)])
        if op == Diff.ADD:
            jp.append({"op": "add", "path": p, "value": e.value})
        elif op == Diff.REPLACE:
            jp.append({"op": "replace", "path": p, "value": e.value})
        elif op == Diff.REMOVE:
            jp.append({"op": "remove", "path": p})
        elif op == Diff.ADDRANGE:
            # JSONPatch only has single value add, no addrange
            # FIXME: Reverse this or not? Read RFC carefully and/or test with some conforming tool.
            #for value in reversed(e.valuelist):
            for value in e.valuelist:
                jp.append({"op": "add", "path": p, "value": value})
        elif op == Diff.REMOVERANGE:
            # JSONPatch only has single value remove, no removerange
            for i in range(e.length):
                p_i = "/".join((path, str(e.key + i)))  # Note: not using p
                jp.append({"op": "remove", "path": p_i})
        elif op == Diff.PATCH:
            # JSONPatch has no recursion, recurse here to flatten diff
            jp.extend(to_json_patch(e.diff, p))
    return jp
