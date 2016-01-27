# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types
from six.moves import xrange as range

from .log import NBDiffFormatError


# Valid values for the action field in diff entries
INSERT = "add"
DELETE = "remove"
REPLACE = "replace"
PATCH = "patch"
SEQINSERT = "addrange"
SEQDELETE = "removerange"

ACTIONS = [
    PATCH,
    INSERT,
    DELETE,
    REPLACE,
    SEQINSERT,
    SEQDELETE,
    ]

SEQUENCE_ACTIONS = [
    SEQINSERT,
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
        self.diff.append(entry)

    def add(self, at, values):
        self.diff.append([SEQINSERT, at, values])

    def remove(self, at, num_values):
        self.diff.append([SEQDELETE, at, num_values])

    def patch(self, at, diff):
        self.diff.append([PATCH, at, diff])


class MappingDiff(Diff):
    def __init__(self):
        self.diff = []

    def __len__(self):
        return len(self.diff)

    def __iter__(self):
        return iter(self.diff)

    def add(self, key, value):
        self.diff.append([INSERT, key, value])

    def remove(self, key):
        self.diff.append([DELETE, key])

    def replace(self, key, new_value):
        self.diff.append([REPLACE, key, new_value])

    def patch(self, at, diff):
        self.diff.append([PATCH, at, diff])


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
    for s in diff:
        validate_diff_entry(s, deep=deep)


def validate_diff_entry(s, deep=False):
    """Check that s is a well formed diff entry.

    The diff entry format is a list
    s[0] # op (one of PATCH, INSERT, DELETE, REPLACE)
    s[1] # key (str for diff of dict, int for diff of sequence (list or str))
    s[2] # op specific argument, omitted if op is DELETE

    For sequences (lists and strings) the ops
    SEQINSERT and SEQDELETE are also allowed.
    """
    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(s, list):
        raise NBDiffFormatError("Diff entry '{}' is not a list.".format(s))
    n = len(s)
    if not (n == 3 or (n == 2 and s[0] == DELETE)):
        raise NBDiffFormatError("Diff entry '{}' has the wrong size.".format(s))

    op = s[0]

    # Check key (list or str uses int key, dict uses str key)
    is_sequence = isinstance(s[1], int)
    is_mapping = isinstance(s[1], string_types)
    if not (is_sequence or is_mapping):
        raise NBDiffFormatError("Diff entry key '{}' has type '{}', expecting int or unicode/str.".format(s[1], type(s[1])))

    # Sequence diff ops ++, --, :: are not valid for mapping diffs
    if is_mapping and op not in MAPPING_ACTIONS:
        raise NBDiffFormatError("Diff op '{}' only valid in diff of sequence.".format(op))

    if op == INSERT:
        # s[2] is a single value to insert at key
        pass
    elif op == DELETE:
        # no s[2] argument
        pass
    elif op == REPLACE:
        # s[2] is a single value to replace value at key with
        pass
    elif op == PATCH:
        # s[2] is itself a diff, check it recursively if the "deep" argument is true
        # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
        if deep:
            validate_diff(s[2], deep=deep)
    # Experimental sequence diff ops
    elif op == SEQINSERT:
        # For sequence insert, s[2] is a list of values to insert.
        if not isinstance(s[2], sequence_types):
            raise NBDiffFormatError("Diff sequence insert expects list of values, not '{}'.".format(s[2]))
    elif op == SEQDELETE:
        # s[2] is the number of items to delete from sequence
        if not isinstance(s[2], int):
            raise NBDiffFormatError("Diff sequence delete expects integer number of values, not '{}'.".format(s[2]))
    else:
        # Unknown op
        raise NBDiffFormatError("Unknown diff op '{}'.".format(op))

    # Note that false positives are possible, for example
    # we're not checking the values in any way


def to_dict_diff(ld):
    """Convert a dict diff from list format [[op, key, arg]] to dict format {key:[op,arg]}.

    The conversion is shallow, i.e. diffs within PATCH entries are not modified.
    """
    dd = {}
    for e in ld:
        op = e[0]
        if len(e) == 2:
            dd[e[1]] = [op]
        elif len(e) == 3:
            dd[e[1]] = [op, e[2]]
        else:
            raise ValueError("Invalid diff format.")
    return dd


def count_consumed_symbols(e):
    "Count how many symbols are consumed from each sequence by a single sequence diff entry."
    op = e[0]
    if op == SEQINSERT:
        return 0, len(e[2])
    elif op == SEQDELETE:
        return e[2], 0
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


def to_json_patch_format(d, path=""):
    """Convert nbdime diff object into the RFC6902 JSON Patch format.

    This is untested and will need some details worked out.
    """
    jp = []
    for e in d:
        op = e[0]
        k = e[1]
        p = "/".join([path, str(k)])
        if op == INSERT:
            jp.append({"op": "add", "path": p, "value": e[2]})
        elif op == REPLACE:
            jp.append({"op": "replace", "path": p, "value": e[2]})
        elif op == DELETE:
            jp.append({"op": "remove", "path": p})
        elif op == SEQINSERT:
            for value in e[2]: # FIXME: Reverse this or not? Read RFC carefully and/or test with some conforming tool.
                jp.append({"op": "add", "path": p, "value": e[2]})
        elif op == SEQDELETE:
            for i in range(e[1], e[1]+e[2]):
                jp.append({"op": "remove", "path": "/".join((path, str(i)))})
        elif op == PATCH:
            jp.extend(to_json_patch_format(e[2], p))
    return jp
