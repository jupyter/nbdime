# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import difflib

__all__ = ["is_atomic", "is_similar"]


def is_atomic(x):
    atomic_strings = False # TODO: Configuration framework?

    if atomic_strings:
        return not isinstance(x, (list, dict))
    else:
        return not isinstance(x, (basestring, list, dict))


def strings_are_similar(x, y):

    # TODO: How does e.g. git or meld handle this?

    # TODO: Configuration framework? Tune heuristics.
    enable_char_diff = True
    threshold = 0.90

    # Informal benchmark normalized to ==:
    #    1.0  ==
    #  438.2  real_quick_ratio
    #  796.5  quick_ratio
    # 3088.2  ratio
    # The == cutoff will hit most of the time for long runs of
    # equal items, at least in the Myers diff algorithm.
    # Most other comparisons will likely not be very similar,
    # and the (real_)quick_ratio cutoffs will speed up those.
    # So the heavy ratio function is only used for close calls.
    # TODO: Is Levenschtein ratio better than SequenceMatcher?

    if x == y:
        return True
    elif enable_char_diff:
        s = difflib.SequenceMatcher(lambda c: c in (" ", "\t"), x, y, autojunk=False)
        if s.real_quick_ratio() < threshold:
            return False
        if s.quick_ratio() < threshold:
            return False
        return s.ratio() > threshold
    else:
        return False


def is_similar(x, y):
    """Returns True if x and y are deemed sufficiently similar to be
    considered a changed instead of replaced element in a sequence diff.

    This function is intended as an example, not as a generic solution
    to comparing objects for simliarity.

    TODO: Pass path to compare functions?
    A generic implementation like this one doesn't know
    the context in which 'similar' is defined.
    """

    # TODO: There are a lot of quality and performance issues that
    # will involve a good implementation of this function, or multiple
    # implementations of this function for different contexts.
    # This will require a broad investigation.
    # This implementation is only a temporary rough draft.

    if type(x) != type(y):
        return False

    if isinstance(x, basestring):
        return strings_are_similar(x, y)

    elif isinstance(x, list):
        # TODO: Implement custom ratio function, diff-like with cutoff?
        # (For shallow lists of strings, SequenceMatcher could work.)
        return x == y

    elif isinstance(x, dict):
        # TODO: Implement custom ratio function, diff-like with cutoff?
        # (For shallow dicts of atomic values, and with some ordering of the items, SequenceMatcher could work.)
        return x == y

    else:
        return x == y
