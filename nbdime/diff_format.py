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


# Just to make sure we don't use the namedtuple instances directly,
# at least for now I consider this a refactoring step that may be
# replaced with something else such as a dict with setattr support like notebooks have.
def _make_diff_types():
    # These are similar to the JSON Patch format except for the use of direct key instead of deep paths:
    op_add     = namedtuple("add",    ("op", "key", "value"))
    op_remove  = namedtuple("remove", ("op", "key"))
    op_replace = namedtuple("replace", ("op", "key", "value"))
    
    # These are nbdime additions not in JSON Patch
    op_patch       = namedtuple("patch",       ("op", "key", "diff"))
    op_addrange    = namedtuple("addrange",    ("op", "key", "valuelist"))
    op_removerange = namedtuple("removerange", ("op", "key", "length"))

    # Collection used for validation
    mapping_diff_types = (op_add, op_remove, op_replace, op_patch, DiffEntry)
    sequence_diff_types = (op_addrange, op_removerange, op_patch, DiffEntry)
    diff_types = tuple(set(mapping_diff_types + sequence_diff_types))
    diff_types_by_key = {t.__name__: t for t in diff_types}
    return mapping_diff_types, sequence_diff_types, diff_types, diff_types_by_key

mapping_diff_types, sequence_diff_types, diff_types, diff_types_by_key = _make_diff_types()

def make_op(op, *args):
    "Create a diff entry."
    # FIXME: refactor and make less convoluted
    e = diff_types_by_key[op](op, *args)
    #return e
    return DiffEntry(e._asdict())

# Valid values for the action field in diff entries
ADD = "add"
REMOVE = "remove"
REPLACE = "replace"
PATCH = "patch"
ADDRANGE = "addrange"
REMOVERANGE = "removerange"



sequence_types = string_types + (list,)


class Diff(object):
    pass


class SequenceDiff(Diff):

    # Valid values for the action field in diff entries
    ADDRANGE = "addrange"
    REMOVERANGE = "removerange"
    PATCH = "patch"

    OPS = (
        ADDRANGE,
        REMOVERANGE,
        PATCH,
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
        assert isinstance(entry, sequence_diff_types)
        self.diff.append(entry)

    def add(self, key, valuelist):
        self.append(make_op(ADDRANGE, key, valuelist))

    def remove(self, key, length):
        self.append(make_op(REMOVERANGE, key, length))

    def patch(self, key, diff):
        self.append(make_op(PATCH, key, diff))


class MappingDiff(Diff):

    # Valid values for the action field in diff entries
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    PATCH = "patch"

    OPS = (
        PATCH,
        ADD,
        REMOVE,
        REPLACE,
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
        assert isinstance(entry, mapping_diff_types)
        self.diff.append(entry)
        #self.diff[entry.key] = entry

    def add(self, key, value):
        self.append(make_op(ADD, key, value))

    def remove(self, key):
        self.append(make_op(REMOVE, key))

    def replace(self, key, value):
        self.append(make_op(REPLACE, key, value))

    def patch(self, key, diff):
        self.append(make_op(PATCH, key, diff))


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


def validate_diff_entry(e, deep=False):
    """Check that e is a well formed diff entry.

    All diff entry object have the two attributes, e.op and e.key.

    For the diff of a sequence (list, string) of length N, these should be:

        e.op = one of ADDRANGE, REMOVERANGE, PATCH
        e.key = integer index in range 0-N inclusive

    For the diff of a dict, these should be:

        e.op = one of PATCH, ADD, REMOVE, REPLACE
        e.key = string, must match existing key for PATCH, REMOVE, REPLACE, and not match for ADD

    In addition most of the ops have specific attributes:

        ADD: e.value, the new value to add at e.key
        REPLACE: e.value, the new value to replace the existing value at e.key with
        REMOVE: nothing
        PATCH: e.diff, the diff object to patch the existing value at e.key with
        ADDRANGE: e.valuelist, the list of new values to add before e.key
        REMOVERANGE: e.length, the number of values to remove starting at index e.key

    """
    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(e, diff_types):
        raise NBDiffFormatError("Diff entry '{}' is not a diff type.".format(e))

    # Check key (list or str uses int key, dict uses str key)
    op = e.op
    key = e.key
    if isinstance(key, int) and op in SequenceDiff.OPS:
        if op == SequenceDiff.ADDRANGE:
            if not isinstance(e.valuelist, sequence_types):
                raise NBDiffFormatError("addrange expects a sequence of values to insert, not '{}'.".format(e.valuelist))
        elif op == SequenceDiff.REMOVERANGE:
            if not isinstance(e.length, int):
                raise NBDiffFormatError("removerange expects a number of values to delete, not '{}'.".format(e.length))
        elif op == SequenceDiff.PATCH:
            # e.diff is itself a diff, check it recursively if the "deep" argument is true
            # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
            if deep:
                validate_diff(e.diff, deep=deep)
        else:
            raise NBDiffFormatError("Unknown diff op '{}'.".format(op))
    elif isinstance(key, string_types) and op in MappingDiff.OPS:
        if op == MappingDiff.ADD:
            pass  # e.value is a single value to insert at key
        elif op == MappingDiff.REMOVE:
            pass  # no argument
        elif op == MappingDiff.REPLACE:
            # e.value is a single value to replace value at key with
            pass
        elif op == MappingDiff.PATCH:
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
    if op == ADDRANGE:
        return (0, len(e.valuelist))
    elif op == REMOVERANGE:
        return (e.length, 0)
    elif op == PATCH:
        return (1, 1)
    else:
        raise NBDiffFormatError("Invalid op '{}'".format(op))


def source_as_string(source):
    "Return source as a single string, joined as lines if it's a list."
    if isinstance(source, list):
        source = "\n".join(line.strip("\n") for line in source)
    assert isinstance(source, string_types)
    return source


def to_json_patch(d, path=""):
    """Convert nbdime diff object into the RFC6902 JSON Patch format.

    This is untested and will need some details worked out.
    """
    jp = []
    for e in d:
        op = e.op
        p = "/".join([path, str(e.key)])
        if op == ADD:
            jp.append({"op": "add", "path": p, "value": e.value})
        elif op == REPLACE:
            jp.append({"op": "replace", "path": p, "value": e.value})
        elif op == REMOVE:
            jp.append({"op": "remove", "path": p})
        elif op == ADDRANGE:
            # JSONPatch only has single value add, no addrange
            # FIXME: Reverse this or not? Read RFC carefully and/or test with some conforming tool.
            #for value in reversed(e.valuelist):
            for value in e.valuelist:
                jp.append({"op": "add", "path": p, "value": value})
        elif op == REMOVERANGE:
            # JSONPatch only has single value remove, no removerange
            for i in range(e.length):
                p_i = "/".join((path, str(e.key + i)))  # Note: not using p
                jp.append({"op": "remove", "path": p_i})
        elif op == PATCH:
            # JSONPatch has no recursion, recurse here to flatten diff
            jp.extend(to_json_patch(e.diff, p))
    return jp
