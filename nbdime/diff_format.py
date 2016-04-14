# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range

from .log import NBDiffFormatError


class DiffEntry(dict):
    """For internal usage in nbdime library.

    Minimal class providing attribute access to diff entiry keys.

    Tip: If performance dictates, we can easily replace this
    with a namedtuple during processing of diffs and convert
    to dicts before any json conversions.
    """
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class DiffOp:
    "Collection of valid values for the action field in diff entries."
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    ADDRANGE = "addrange"
    REMOVERANGE = "removerange"
    PATCH = "patch"

    # For future consideration
    #KEEP = "keep"
    #KEEPRANGE = "keeprange"
    #MOVE = "move"
    #MOVERANGE = "moverange"


#def op_keep(key):
#    "Create a diff entry to keep value at key."
#    return DiffEntry(op=DiffOp.KEEP, key=key)

def op_add(key, value):
    "Create a diff entry to add value at/before key."
    return DiffEntry(op=DiffOp.ADD, key=key, value=value)

def op_remove(key):
    "Create a diff entry to remove value at key."
    return DiffEntry(op=DiffOp.REMOVE, key=key)

def op_replace(key, value):
    "Create a diff entry to replace value at key with given value."
    return DiffEntry(op=DiffOp.REPLACE, key=key, value=value)

#def op_keeprange(key, length):
#    "Create a diff entry to keep values in range key:key+length."
#    return DiffEntry(op=DiffOp.KEEPRANGE, key=key, length=length)

def op_addrange(key, valuelist):
    "Create a diff entry to add given list of values before key."
    return DiffEntry(op=DiffOp.ADDRANGE, key=key, valuelist=valuelist)

def op_removerange(key, length):
    "Create a diff entry to remove values in range key:key+length."
    return DiffEntry(op=DiffOp.REMOVERANGE, key=key, length=length)

def op_patch(key, diff):
    "Create a diff entry to patch value at key with diff."
    return DiffEntry(op=DiffOp.PATCH, key=key, diff=diff)


class SequenceDiffBuilder(object):

    # Valid values for the action field in sequence diff entries
    OPS = (
        DiffOp.ADDRANGE,
        DiffOp.REMOVERANGE,
        #DiffOp.KEEPRANGE,
        DiffOp.PATCH,
        )

    def __init__(self):
        self.diff = []

    def __len__(self):
        return len(self.diff)

    def __iter__(self):
        return iter(self.diff)

    def __getitem__(self, i):
        return self.diff[i]

    def validated(self):
        # TODO: Use .validated() instead of .diff in algorithms and add invariant checking here
        return self.diff
    
    def append(self, entry):
        assert isinstance(entry, DiffEntry)

        # Assert consistent ordering
        assert len(self.diff) == 0 or self.diff[-1].key <= entry.key

        # Add entry
        self.diff.append(entry)

        # Swap last two entries if insertion was inserted
        # at same location as a previous remove or patch
        if (entry.op == DiffOp.ADDRANGE and
            len(self.diff) >= 2 and entry.key == self.diff[-2].key
            ):
            self.diff[-2], self.diff[-1] = self.diff[-1], self.diff[-2]

    def patch(self, key, diff):
        if diff:
            self.append(op_patch(key, diff))

    def addrange(self, key, valuelist):
        if valuelist:
            self.append(op_addrange(key, valuelist))

    def removerange(self, key, length):
        if length:
            self.append(op_removerange(key, length))

    def keeprange(self, key, length):
        if length:
            self.append(op_keeprange(key, length))


class MappingDiffBuilder(object):

    # Valid values for the action field in mapping diff entries
    OPS = (
        #DiffOp.KEEP,
        DiffOp.ADD,
        DiffOp.REMOVE,
        DiffOp.REPLACE,
        DiffOp.PATCH,
        )

    def __init__(self):
        self.diff = []
        #self.diff = {}

    def __len__(self):
        return len(self.diff)

    def __iter__(self):
        return iter(self.diff)
        #return iter(self.diff.values())

    def validated(self):
        # TODO: Use .validated() instead of .diff in algorithms and add invariant checking here
        return self.diff

    def append(self, entry):
        assert isinstance(entry, DiffEntry)
        self.diff.append(entry)
        #self.diff[entry.key] = entry

    def keep(self, key):
        self.append(op_keep(key))

    def add(self, key, value):
        self.append(op_add(key, value))

    def remove(self, key):
        self.append(op_remove(key))

    def replace(self, key, value):
        self.append(op_replace(key, value))

    def patch(self, key, diff):
        if diff:
            self.append(op_patch(key, diff))


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
        raise NBDiffFormatError("DiffOp must be a list.")
    for e in diff:
        validate_diff_entry(e, deep=deep)


sequence_types = string_types + (list,)


def validate_diff_entry(e, deep=False):
    """Check that e is a well formed diff entry, as documented under docs/."""

    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(e, DiffEntry):
        raise NBDiffFormatError("DiffOp entry '{}' is not a diff type.".format(e))

    # Check key (list or str uses int key, dict uses str key)
    op = e.op
    key = e.key
    if isinstance(key, int) and op in SequenceDiffBuilder.OPS:
        if op == DiffOp.ADDRANGE:
            if not isinstance(e.valuelist, sequence_types):
                raise NBDiffFormatError("addrange expects a sequence of values to insert, not '{}'.".format(e.valuelist))
        elif op == DiffOp.REMOVERANGE:
            if not isinstance(e.length, int):
                raise NBDiffFormatError("removerange expects a number of values to delete, not '{}'.".format(e.length))
        elif op == DiffOp.PATCH:
            # e.diff is itself a diff, check it recursively if the "deep" argument is true
            # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
            if deep:
                validate_diff(e.diff, deep=deep)
        else:
            raise NBDiffFormatError("Unknown diff op '{}'.".format(op))
    elif isinstance(key, string_types) and op in MappingDiffBuilder.OPS:
        if op == DiffOp.ADD:
            pass  # e.value is a single value to insert at key
        elif op == DiffOp.REMOVE:
            pass  # no argument
        elif op == DiffOp.REPLACE:
            # e.value is a single value to replace value at key with
            pass
        elif op == DiffOp.PATCH:
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
    if op == DiffOp.ADDRANGE:
        return (0, len(e.valuelist))
    elif op == DiffOp.REMOVERANGE:
        return (e.length, 0)
    elif op == DiffOp.PATCH:
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


def decompress_sequence_diff(di, n):
    """Convert sequence diff into pairs of (op, arg) for each n entries in base sequence.

    This is for internal use in algorithms where no
    insertions occur, making the mapping

        index -> (op, arg)

    possible with op in (KEEP, REMOVE, PATCH, REPLACE).
    """
    offset = 0
    decompressed = [op_keep(i) for i in range(n)]
    for e in di:
        op = e.op
        if op in (DiffOp.PATCH, DiffOp.REPLACE, DiffOp.REMOVE):
            decompressed[e.key] = e
        elif op == DiffOp.REMOVERANGE:
            for i in range(e.length):
                decompressed[e.key + i] = op_remove(e.key + i)
        elif op in (DiffOp.ADDRANGE, DiffOp.ADD):
            raise ValueError("Not expexting insertions.")
        else:
            raise ValueError("Unknown op {}.".format(op))
    return decompressed


def as_dict_based_diff(di):
    """Converting to dict-based diff format for dicts for convenience.

    NB! Only one level, not recursive.

    This step will be unnecessary if we change the diff format to work this way always.
    """
    return {e.key: e for e in di}


def revert_as_dict_based_diff(di):
    "Reverts as_dict_based_diff."
    return [di[k] for k in sorted(di)]


def to_json_patch(d, path=""):
    """Convert nbdime diff object into the RFC6902 JSON Patch format.

    This is untested and will need some details worked out.
    """
    raise RuntimeError("to_json_patch is currently not correct, see github issue.")
    jp = []
    for e in d:
        op = e.op
        p = "/".join([path, str(e.key)])
        if op == DiffOp.ADD:
            jp.append({"op": "add", "path": p, "value": e.value})
        elif op == DiffOp.REPLACE:
            jp.append({"op": "replace", "path": p, "value": e.value})
        elif op == DiffOp.REMOVE:
            jp.append({"op": "remove", "path": p})
        elif op == DiffOp.ADDRANGE:
            # JSONPatch only has single value add, no addrange
            # FIXME: Reverse this or not? Read RFC carefully and/or test with some conforming tool.
            #for value in reversed(e.valuelist):
            for value in e.valuelist:
                jp.append({"op": "add", "path": p, "value": value})
        elif op == DiffOp.REMOVERANGE:
            # JSONPatch only has single value remove, no removerange
            for i in range(e.length):
                p_i = "/".join((path, str(e.key + i)))  # Note: not using p
                jp.append({"op": "remove", "path": p_i})
        elif op == DiffOp.PATCH:
            # JSONPatch has no recursion, recurse here to flatten diff
            jp.extend(to_json_patch(e.diff, p))
    return jp

