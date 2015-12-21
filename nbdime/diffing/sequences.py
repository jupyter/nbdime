# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

__all__ = ["diff_strings", "diff_sequence"]

import operator
from six import string_types

from .seq_difflib import diff_sequence_difflib
from .seq_bruteforce import diff_sequence_bruteforce
from .seq_myers import diff_sequence_myers

# TODO: Configuration framework?
diff_sequence_algorithm = "bruteforce" #"difflib" #"myers"


def diff_sequence(a, b, compare=operator.__eq__):
    """Compute a diff of two sequences.

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
    return diff_sequence_difflib(a, b)
