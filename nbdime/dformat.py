# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from six import string_types
from six.moves import xrange as range

from .log import error

def error_invalid_diff_entry(s):
    error("Invalid diff entry '{}'.".format(s))

def is_valid_diff(diff, deep=False):
    try:
        validate_diff(diff, deep=deep)
        result = True
    except:
        result = False
    return result

def validate_diff(diff, deep=False):
    if not isinstance(diff, list):
        error("Diff must be a list.")
    for s in diff:
        validate_diff_entry(s, deep=deep)

def validate_diff_entry(s, deep=False):
    """Check that s is a well formed diff entry.

    The diff entry format is a list
    s[0] # action (one of "+" (insert), "-" (delete), ":" (replace), "!" (patch))
    s[1] # key (str for diff of dict, int for diff of sequence (list or str))
    s[2] # action specific argument, omitted if action is "-"

    Additional experimental sequence actions "++", "--", "::" are also allowed.
    """
    # Sequence types, allowing both list and string in sequence insert ("++")
    sequence = string_types + (list,)

    # Entry is always a list with 3 items, or 2 in the special case of single item deletion
    if not isinstance(s, list):
        error("Diff entry '{}' is not a list.".format(s))
    n = len(s)
    if not (n == 3 or (n == 2 and s[0] == "-")):
        error("Diff entry '{}' has the wrong size.".format(s))

    # Check key (list or str uses int key, dict uses str key)
    is_sequence = isinstance(s[1], int)
    is_mapping = isinstance(s[1], string_types)
    if not (is_sequence or is_mapping):
        error("Diff entry key '{}' has type '{}', expecting int or unicode/str.".format(s[1], type(s[1])))

    # Experimental sequence diff actions ++, --, :: are not valid for mapping diffs
    if is_mapping and len(s[0]) > 1:
        error("Diff action '{}' only valid in diff of sequence.".format(s[0]))

    if s[0] == "+":
        # s[2] is a single value to insert at key
        pass
    elif s[0] == "-":
        # no s[2] argument
        pass
    elif s[0] == ":":
        # s[2] is a single value to replace value at key with
        pass
    elif s[0] == "!":
        # s[2] is itself a diff, check it recursively if the "deep" argument is true
        # (the "deep" argument is here to avoid recursion and potential O(>n) performance pitfalls)
        if deep:
            validate_diff(s[2], deep=deep)
    # Experimental sequence diff actions
    elif s[0] == "++":
        # For sequence insert, s[2] is a list of values to insert.
        if not isinstance(s[2], sequence):
            error("Diff sequence insert expects list of values, not '{}'.".format(s[2]))
    elif s[0] == "--":
        # s[2] is the number of items to delete from sequence
        if not isinstance(s[2], int):
            error("Diff sequence delete expects integer number of values, not '{}'.".format(s[2]))
    elif s[0] == "::":
        # For sequence replace, s[2] is a list of values to
        # replace the next len(s[2]) values starting at key.
        if not isinstance(s[2], sequence):
            error("Diff sequence replace expects list of values, not '{}'.".format(s[2]))
    else:
        # Unknown action
        error("Unknown diff action '{}'.".format(s[0]))

    # Note that false positives are possible, for example
    # we're not checking the values in any way

def decompress_diff(sequence_diff):
    """Split all sequence diff actions ++,--,:: into single-line actions +,-,:.

    Current implementation applies only to a single-level sequence list diff.
    """
    d = []
    for s in sequence_diff:
        action = s[0]
        if action in ("+", "-", ":", "!"):
            d.append(s)
        elif action == "++":
            for i, v in enumerate(s[2]):
                d.append(["+", s[1], v])
        elif action == "--":
            for i in range(s[2]):
                d.append(["-", s[1] + i])
        elif action == "::":
            for i, v in enumerate(s[2]):
                d.append([":", s[1] + i, v])
        else:
            raise RuntimeError("Invalid action '{}'".format(action))
    return d

#def compress_diff(diff):
#    """Combine contiguous single-line actions +,-,: into sequence diff actions ++,--,:: everywhere."""
#    TODO

def count_consumed_symbols(e):
    "Count how many symbols are consumed from each sequence by a single sequence diff entry."
    action = e[0]
    if action == "+":
        return 0, 1
    elif action == "-":
        return 1, 0
    elif action == ":":
        return 1, 1
    elif action == "!":
        return 1, 1
    elif action == "++":
        return 0, len(e[2])
    elif action == "--":
        return e[2], 0
    elif action == "::":
        return len(e[2]), len(e[2])
    else:
        error_invalid_diff_entry(e)

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
