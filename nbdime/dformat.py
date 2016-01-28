# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range
from collections import namedtuple

from .log import NBDiffFormatError


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
    op_addrange    = namedtuple("addrange",    ("op", "key", "values"))
    op_removerange = namedtuple("removerange", ("op", "key", "length"))

    # Collection used for validation
    mapping_diff_types = (op_add, op_remove, op_replace, op_patch)
    sequence_diff_types = (op_addrange, op_removerange, op_patch)
    diff_types = tuple(set(mapping_diff_types + sequence_diff_types))
    diff_types_by_key = {t.__name__: t for t in diff_types}
    return mapping_diff_types, sequence_diff_types, diff_types, diff_types_by_key

mapping_diff_types, sequence_diff_types, diff_types, diff_types_by_key = _make_diff_types()

def make_op(op, *args):
    "Create a diff entry."
    return diff_types_by_key[op](op, *args)


# Valid values for the action field in diff entries
INSERT = "add"
DELETE = "remove"
REPLACE = "replace"
PATCH = "patch"
ADDRANGE = "addrange"
SEQDELETE = "removerange"

ACTIONS = [
    PATCH,
    INSERT,
    DELETE,
    REPLACE,
    ADDRANGE,
    SEQDELETE,
    ]

SEQUENCE_ACTIONS = [
    ADDRANGE,
    SEQDELETE,
    PATCH
    ]

MAPPING_ACTIONS = [
    INSERT,
    DELETE,
    REPLACE,
    PATCH
    ]


sequence_types = string_types + (list,)


class Diff(object):
    pass


class SequenceDiff(Diff):
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

    def add(self, key, values):
        self.append(make_op(ADDRANGE, key, values))

    def remove(self, key, num_values):
        self.append(make_op(SEQDELETE, key, num_values))

    def patch(self, key, diff):
        self.append(make_op(PATCH, key, diff))


class MappingDiff(Diff):
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
        self.append(make_op(INSERT, key, value))

    def remove(self, key):
        self.append(make_op(DELETE, key))

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
    return result


def validate_diff(diff, deep=False):
    if not isinstance(diff, list):
        raise NBDiffFormatError("Diff must be a list.")
    for e in diff:
        validate_diff_entry(e, deep=deep)


def validate_diff_entry(e, deep=False):
    """Check that e is a well formed diff entry.

    The diff entry format is a list
    e[0] # op (one of PATCH, INSERT, DELETE, REPLACE)
    e[1] # key (str for diff of dict, int for diff of sequence (list or str))
    e[2] # op specific argument, omitted if op is DELETE

    For sequences (lists and strings) the ops
    ADDRANGE and SEQDELETE are also allowed.
    """
    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(e, diff_types):
        raise NBDiffFormatError("Diff entry '{}' is not a diff type.".format(e))

    # This is not possible for namedtuple types:
    #n = len(e)
    #if not (n == 3 or (n == 2 and e[0] == DELETE)):
    #    raise NBDiffFormatError("Diff entry '{}' has the wrong size.".format(e))

    op = e.op
    key = e.key

    # Check key (list or str uses int key, dict uses str key)
    if not (    (isinstance(key, int)          and op in SEQUENCE_ACTIONS)
             or (isinstance(key, string_types) and op in MAPPING_ACTIONS) ):
        raise NBDiffFormatError("Invalid diff entry key '{}' of type '{}', expecting int for sequences or unicode/str for mappings.".format(key, type(key)))

    if op == INSERT:
        pass  # e.value is a single value to insert at key
    elif op == DELETE:
        pass  # no argument
    elif op == REPLACE:
        # e.value is a single value to replace value at key with
        pass
    elif op == PATCH:
        # e.diff is itself a diff, check it recursively if the "deep" argument is true
        # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
        if deep:
            validate_diff(e.diff, deep=deep)
    elif op == ADDRANGE:
        if not isinstance(e.values, sequence_types):
            raise NBDiffFormatError("addrange expects a sequence of values to insert, not '{}'.".format(e.values))
    elif op == SEQDELETE:
        if not isinstance(e.length, int):
            raise NBDiffFormatError("removerange expects a number of values to delete, not '{}'.".format(e.length))
    else:
        raise NBDiffFormatError("Unknown diff op '{}'.".format(op))

    # Note that false positives are possible, for example
    # we're not checking the values in any way, as they
    # can in principle be arbitrary json objects


def count_consumed_symbols(e):
    "Count how many symbols are consumed from each sequence by a single sequence diff entry."
    op = e.op
    if op == ADDRANGE:
        return 0, len(e.values)
    elif op == SEQDELETE:
        return e.length, 0
    elif op == PATCH:
        return 1, 1
    else:
        raise NBDiffFormatError("Invalid op '{}'".format(op))


def source_as_string(source):
    "Return source as a single string, joined as lines if it's a list."
    if isinstance(source, list):
        source = "\n".join(line.strip("\n") for line in source)
    assert isinstance(source, string_types)
    return source


def to_json_patch_format(d, path="/"):
    """Convert nbdime diff object into the RFC6902 JSON Patch format.

    This is untested and will need some details worked out.
    """
    jp = []
    for e in d:
        op = e.op
        p = "/".join([path, str(e.key)])
        if op == INSERT:
            jp.append({"op": "add", "path": p, "value": e.value})
        elif op == REPLACE:
            jp.append({"op": "replace", "path": p, "value": e.value})
        elif op == DELETE:
            jp.append({"op": "remove", "path": p})
        elif op == ADDRANGE:
            # JSONPatch only has single value add, no addrange
            # FIXME: Reverse this or not? Read RFC carefully and/or test with some conforming tool.
            #for value in reversed(e.values):
            for value in e.values:
                jp.append({"op": "add", "path": p, "value": value})
        elif op == SEQDELETE:
            # JSONPatch only has single value remove, no removerange
            for i in range(e.length):
                p_i = "/".join((path, str(e.key + i)))  # Note: not using p
                jp.append({"op": "remove", "path": p_i})
        elif op == PATCH:
            # JSONPatch has no recursion, recurse here to flatten diff
            jp.extend(to_json_patch_format(e.diff, p))
    return jp
