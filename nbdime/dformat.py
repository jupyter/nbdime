# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from six import string_types
from six.moves import xrange as range

from .log import error, NBDiffFormatError

# Valid values for the action field in diff entries
PATCH = u"!"
INSERT = u"+"
DELETE = u"-"
REPLACE = u":"
SEQINSERT = u"++"
SEQDELETE = u"--"

ACTIONS = [
    PATCH,
    INSERT,
    DELETE,
    REPLACE,
    SEQINSERT,
    SEQDELETE,
    ]

sequence_types = string_types + (list,)


def is_valid_diff(diff, deep=False):
    try:
        validate_diff(diff, deep=deep)
        result = True
    except NBDiffFormatError as e:
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
    s[0] # action (one of PATCH, INSERT, DELETE, REPLACE)
    s[1] # key (str for diff of dict, int for diff of sequence (list or str))
    s[2] # action specific argument, omitted if action is "-"

    For sequences (lists and strings) the actions
    SEQINSERT and SEQDELETE are also allowed.
    """
    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(s, list):
        raise NBDiffFormatError("Diff entry '{}' is not a list.".format(s))
    n = len(s)
    if not (n == 3 or (n == 2 and s[0] == DELETE)):
        raise NBDiffFormatError("Diff entry '{}' has the wrong size.".format(s))

    # Check key (list or str uses int key, dict uses str key)
    is_sequence = isinstance(s[1], int)
    is_mapping = isinstance(s[1], string_types)
    if not (is_sequence or is_mapping):
        raise NBDiffFormatError("Diff entry key '{}' has type '{}', expecting int or unicode/str.".format(s[1], type(s[1])))

    # Experimental sequence diff actions ++, --, :: are not valid for mapping diffs
    if is_mapping and len(s[0]) > 1:
        raise NBDiffFormatError("Diff action '{}' only valid in diff of sequence.".format(s[0]))

    if s[0] == INSERT:
        # s[2] is a single value to insert at key
        pass
    elif s[0] == DELETE:
        # no s[2] argument
        pass
    elif s[0] == REPLACE:
        # s[2] is a single value to replace value at key with
        pass
    elif s[0] == PATCH:
        # s[2] is itself a diff, check it recursively if the "deep" argument is true
        # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
        if deep:
            validate_diff(s[2], deep=deep)
    # Experimental sequence diff actions
    elif s[0] == SEQINSERT:
        # For sequence insert, s[2] is a list of values to insert.
        if not isinstance(s[2], sequence_types):
            raise NBDiffFormatError("Diff sequence insert expects list of values, not '{}'.".format(s[2]))
    elif s[0] == SEQDELETE:
        # s[2] is the number of items to delete from sequence
        if not isinstance(s[2], int):
            raise NBDiffFormatError("Diff sequence delete expects integer number of values, not '{}'.".format(s[2]))
    else:
        # Unknown action
        raise NBDiffFormatError("Unknown diff action '{}'.".format(s[0]))

    # Note that false positives are possible, for example
    # we're not checking the values in any way


def decompress_diff(sequence_diff):
    """Split all sequence diff actions ++,--,:: into single-line actions +,-,:.

    Current implementation applies only to a single-level sequence list diff.
    """
    d = []
    for s in sequence_diff:
        action = s[0]
        if action in (INSERT, DELETE, REPLACE, PATCH):
            d.append(s)
        elif action == SEQINSERT:
            for i, v in enumerate(s[2]):
                d.append([INSERT, s[1], v])
        elif action == SEQDELETE:
            for i in range(s[2]):
                d.append([DELETE, s[1] + i])
        else:
            raise NBDiffFormatError("Invalid action '{}'".format(action))
    return d


#def compress_diff(diff):
#    """Combine contiguous single-line actions +,-,: into sequence diff actions ++,--,:: everywhere."""
#    TODO


def count_consumed_symbols(e):
    "Count how many symbols are consumed from each sequence by a single sequence diff entry."
    action = e[0]
    if action == INSERT:
        return 0, 1
    elif action == DELETE:
        return 1, 0
    elif action == REPLACE:
        return 1, 1
    elif action == PATCH:
        return 1, 1
    elif action == SEQINSERT:
        return 0, len(e[2])
    elif action == SEQDELETE:
        return e[2], 0
    else:
        raise NBDiffFormatError("Invalid action '{}'".format(action))


def get_equal_ranges(a, b, d):
    "Return list of tuples [(i,j,n)] such that a[i:i+n] == b[j:j+n] given a diff d of sequences a and b."
    # Count consumed items from a, "take" in patch_list
    acons = 0
    bcons = 0
    ranges = []
    for e in d:
        action = e[0]
        index = e[1]

        # Consume n more unmentioned items.
        # Note that index can be larger than acons in the case where items
        # have been deleted from a and then insertions from b occur.
        n = max(0, index - acons)
        if n > 0:
            ranges.append((acons, bcons, n))

        # Count consumed items
        askip, bskip = count_consumed_symbols(e)
        acons += n + askip
        bcons += n + bskip

    # Consume final items
    n = len(a) - acons
    assert n >= 0
    assert len(b) - bcons == n
    if n > 0:
        ranges.append((acons, bcons, n))

    # Sanity check
    acons += n
    bcons += n
    assert acons == len(a)
    assert bcons == len(b)

    return ranges


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
        elif op == REMOVE:
            jp.append({"op": "remove", "path": p})
        elif op == SEQINSERT:
            for value in e[2]: # FIXME: Reverse this or not? Read RFC carefully and/or test with some conforming tool.
                jp.append({"op": "add", "path": p, "value": e[2]})
        elif op == SEQREMOVE:
            for i in range(e[1], e[1]+e[2]):
                jp.append({"op": "remove", "path": "/".join((path, str(i)))})
        elif op == PATCH:
            jp.extend(to_json_patch_format(e[2], p))
    return jp
