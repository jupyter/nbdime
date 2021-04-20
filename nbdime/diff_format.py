# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from .log import NBDiffFormatError


# Sentinel to allow None as a value
Missing = object()

# Sentinel to represent no diff argument because parent was deleted
ParentDeleted = object()

# Sentinel object used to allow item patching in autoresolve to return None as a valid value
Deleted = object()


class DiffEntry(dict):
    """For internal usage in nbdime library.

    Minimal class providing attribute access to diff entiry keys.

    Tip: If performance dictates, we can easily replace this
    with a namedtuple during processing of diffs and convert
    to dicts before any json conversions.
    """
    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            return self.__getattribute__(name)
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


def op_add(key, value):
    "Create a diff entry to add value at/before key."
    return DiffEntry(op=DiffOp.ADD, key=key, value=value)

def op_remove(key):
    "Create a diff entry to remove value at key."
    return DiffEntry(op=DiffOp.REMOVE, key=key)

def op_replace(key, value):
    "Create a diff entry to replace value at key with given value."
    return DiffEntry(op=DiffOp.REPLACE, key=key, value=value)

def op_addrange(key, valuelist):
    "Create a diff entry to add given list of values before key."
    return DiffEntry(op=DiffOp.ADDRANGE, key=key, valuelist=valuelist)

def op_removerange(key, length):
    "Create a diff entry to remove values in range key:key+length."
    return DiffEntry(op=DiffOp.REMOVERANGE, key=key, length=length)

def op_patch(key, diff):
    "Create a diff entry to patch value at key with diff."
    assert diff is not None, "Patch op needs a diff sequence"
    return DiffEntry(op=DiffOp.PATCH, key=key, diff=diff)


class SequenceDiffBuilder(object):

    # Valid values for the action field in sequence diff entries
    OPS = (
        DiffOp.ADDRANGE,
        DiffOp.REMOVERANGE,
        DiffOp.PATCH,
        )

    def __init__(self):
        self._diff = []

    def validated(self):
        return self._diff

    def append(self, entry):
        # Simplifies some algorithms
        if entry is None:
            return

        # Typechecking (just for internal consistency checking)
        assert isinstance(entry, DiffEntry)
        assert "op" in entry
        assert entry.op in SequenceDiffBuilder.OPS
        assert "key" in entry

        # Insert new entry at sorted position
        n = len(self._diff)
        pos = n
        if entry.op == DiffOp.ADDRANGE:
            # Insert addrange before removerange or patch
            while pos > 0 and self._diff[pos-1].key >= entry.key:
                pos -= 1
        else:
            while pos > 0 and self._diff[pos-1].key > entry.key:
                pos -= 1
        self._diff.insert(pos, entry)

    def patch(self, key, diff):
        if diff:
            self.append(op_patch(key, diff))

    def addrange(self, key, valuelist):
        if valuelist:
            self.append(op_addrange(key, valuelist))

    def removerange(self, key, length):
        if length:
            self.append(op_removerange(key, length))


class MappingDiffBuilder(object):

    # Valid values for the action field in mapping diff entries
    OPS = (
        DiffOp.ADD,
        DiffOp.REMOVE,
        DiffOp.REPLACE,
        DiffOp.PATCH,
        )

    def __init__(self):
        self._diff = {}

    def validated(self):
        return sorted(self._diff.values(), key=lambda x: x.key)

    def append(self, entry):
        # Simplifies some algorithms
        if entry is None:
            return

        # Typechecking (just for internal consistency checking)
        assert isinstance(entry, DiffEntry)
        assert "op" in entry
        assert entry.op in MappingDiffBuilder.OPS
        assert "key" in entry
        assert entry.key not in self._diff

        # Add entry!
        self._diff[entry.key] = entry

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
    """Checks wheter a diff (list of diff entries) is well formed.

    Returns a boolean indicating the well-formedness of the diff.
    """
    try:
        validate_diff(diff, deep=deep)
        result = True
    except NBDiffFormatError:
        result = False
        raise
    return result


def validate_diff(diff, deep=False):
    """Check wheter a diff (list of diff entries) is well formed.

    Raises an NBDiffFormatError if not well formed.
    """
    if not isinstance(diff, list):
        raise NBDiffFormatError("DiffOp must be a list.")
    for e in diff:
        validate_diff_entry(e, deep=deep)


sequence_types = (str, list)


def validate_diff_entry(e, deep=False):
    """Check that e is a well formed diff entry, as documented under docs/.

    Raises an NBDiffFormatError if not well formed.
    """

    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(e, DiffEntry):
        raise NBDiffFormatError("DiffOp entry '{}' is not a diff type.".format(e))

    # Check key (list or str uses int key, dict uses str key)
    op = e.op
    key = e.key
    if isinstance(key, int) and op in SequenceDiffBuilder.OPS:
        if op == DiffOp.ADDRANGE:
            if not isinstance(e.valuelist, sequence_types):
                raise NBDiffFormatError(
                    "addrange expects a sequence of values to insert, not '{}'.".format(
                        e.valuelist))
        elif op == DiffOp.REMOVERANGE:
            if not isinstance(e.length, int):
                raise NBDiffFormatError(
                    "removerange expects a number of values to delete, not '{}'.".format(
                        e.length))
        elif op == DiffOp.PATCH:
            # e.diff is itself a diff, check it recursively if the "deep" argument is true
            # (the "deep" argument is here to avoid recursion and potential
            # O(>n) performance pitfalls)
            if deep:
                validate_diff(e.diff, deep=deep)
        else:
            raise NBDiffFormatError("Unknown diff op '{}'.".format(op))
    elif isinstance(key, str) and op in MappingDiffBuilder.OPS:
        if op == DiffOp.ADD:
            pass  # e.value is a single value to insert at key
        elif op == DiffOp.REMOVE:
            pass  # no argument
        elif op == DiffOp.REPLACE:
            # e.value is a single value to replace value at key with
            pass
        elif op == DiffOp.PATCH:
            # e.diff is itself a diff, check it recursively if the "deep" argument is true
            # (the "deep" argument is here to avoid recursion and potential
            # O(>n) performance pitfalls)
            if deep:
                validate_diff(e.diff, deep=deep)
        else:
            raise NBDiffFormatError("Unknown diff op '{}'.".format(op))
    else:
        msg = ("Invalid diff entry key '{}' of type '{}'. "
               "Expecting int for sequences or unicode/str for mappings.")
        raise NBDiffFormatError(msg.format(key, type(key)))

    # Note that false positives are possible, for example
    # we're not checking the values in any way, as they
    # can in principle be arbitrary json objects
