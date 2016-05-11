# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import operator
from six import string_types

from .seq_difflib import diff_sequence_difflib
from .seq_bruteforce import diff_sequence_bruteforce
from .seq_myers import diff_sequence_myers
from ..diff_format import DiffOp

__all__ = ["diff_strings", "diff_sequence"]


# TODO: Configuration framework?
# legal_diff_sequence_algorithms = ["bruteforce", "difflib", "myers"]
diff_sequence_algorithm = "bruteforce"


def diff_sequence(a, b, compare=operator.__eq__):
    """Compute a shallow diff of two sequences.

    I.e. these algorithms do not recursively diff elements of the sequences.

    This is a wrapper for alternative diff implementations.
    """
    if diff_sequence_algorithm == "difflib":
        if compare is not operator.__eq__:
            raise RuntimeError("Cannot use difflib with comparison other than ==.")
        return diff_sequence_difflib(a, b)
    elif diff_sequence_algorithm == "bruteforce":
        return diff_sequence_bruteforce(a, b, compare)
    elif diff_sequence_algorithm == "myers":
        return diff_sequence_myers(a, b, compare)
    else:
        raise RuntimeError("Unknown diff_sequence_algorithm {}.".format(diff_sequence_algorithm))


def diff_strings(a, b):
    "Compute char-based diff of two strings."
    assert isinstance(a, string_types) and isinstance(b, string_types)
    if a == b:
        return []
    else:
        return diff_sequence_difflib(a, b)


def _translate_splitlines_diff(a, b, d):
    """Translates a diff of strings split by str.splitlines() to single string diff
    """
    for change in d:
        old_key = change.key
        change.key = sum([len(ia) for ia in a[:old_key]])
        if change.op == DiffOp.ADDRANGE:
            change.valuelist = ''.join(change.valuelist)
        elif change.op == DiffOp.REMOVERANGE:
            change.length = len(a[old_key])
    return d


def diff_strings_linewise(a, b):
    """Do a line-wise diff of two strings
    """
    from .generic import diff
    a_lines = a.splitlines(True)
    b_lines = b.splitlines(True)
    return _translate_splitlines_diff(a_lines, b_lines, diff(a_lines, b_lines))
