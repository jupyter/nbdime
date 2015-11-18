# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import operator

__all__ = ["diff_sequence"]

from nbdime.diff.diff_sequence_difflib import diff_sequence_difflib
from nbdime.diff.diff_sequence_bruteforce import diff_sequence_bruteforce
from nbdime.diff.diff_sequence_myers import diff_sequence_myers

# TODO: Configuration framework?
diff_sequence_algoritm = "difflib"

def diff_sequence(a, b, compare=operator.__eq__):
    """Compute a diff of two sequences.

    This is a wrapper for alternative diff implementations.
    """
    if diff_sequence_algoritm == "difflib":
        if compare != operator.__eq__:
            raise RuntimeError("Cannot use difflib with comparison other than ==.")
        return diff_sequence_difflib(a, b)
    elif diff_sequence_algoritm == "bruteforce":
        return diff_sequence_bruteforce(a, b, compare)
    elif diff_sequence_algoritm == "myers":
        return diff_sequence_myers(a, b, compare)
    else:
        raise RuntimeError("Unknown diff_sequence_algorithm {}.".format(diff_sequence_algorithm))
