# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import operator
from collections import defaultdict
import difflib

from ..diff_format import SequenceDiffBuilder, MappingDiffBuilder, validate_diff
from ..diff_utils import count_consumed_symbols

from .config import DiffConfig
from .sequences import diff_strings_linewise, diff_sequence
from .snakes import compute_snakes_multilevel, compute_diff_from_snakes

__all__ = ["diff"]


def default_predicates():
    return defaultdict(lambda: (operator.__eq__,))


def default_differs():
    return defaultdict(lambda: diff)


def compare_strings_approximate(x, y, threshold=0.7, maxlen=None):
    "Compare to strings with approximate heuristics."
    # TODO: Add configuration framework
    # TODO: Tune threshold with realistic sources

    # Fast cutoff when one is empty
    if bool(x) != bool(y):
        return False

    # Cutoff on equality: Python has fast hash functions for strings,
    # and lists of strings also works fine
    if len(x) == len(y) and x == y:
        return True

    # TODO: Investigate performance and quality of this difflib ratio approach,
    # possibly one of the weakest links of the notebook diffing algorithm.
    # Alternatives to try are the libraries diff-patch-match and Levenschtein

    # Informal benchmark normalized to operator ==:
    #    1.0  operator ==
    #  438.2  real_quick_ratio
    #  796.5  quick_ratio
    # 3088.2  ratio
    # The == cutoff will hit most of the time for long runs of
    # equal items, at least in the Myers diff algorithm.
    # Most other comparisons will likely not be very similar,
    # and the (real_)quick_ratio cutoffs will speed up those.

    # So the heavy ratio function is only used for close calls.
    # s = difflib.SequenceMatcher(lambda c: c in (" ", "\t"), x, y, autojunk=False)
    s = difflib.SequenceMatcher(None, x, y, autojunk=False)

    # Use only the fast ratio approximations first
    if s.real_quick_ratio() < threshold:
        return False
    if s.quick_ratio() < threshold:
        return False

    if maxlen is not None and len(x) > maxlen and len(y) > maxlen:
        # We know from above that there is not an exact similarity
        return False

    return s.ratio() > threshold


def diff(a, b, path="", config=None):
    "Compute the diff of two json-like objects, list or dict or string."

    if config is None:
        config = DiffConfig()

    if isinstance(a, list) and isinstance(b, list):
        d = diff_lists(a, b, path=path, config=config)
    elif isinstance(a, dict) and isinstance(b, dict):
        d = diff_dicts(a, b, path=path, config=config)
    elif isinstance(a, str) and isinstance(b, str):
        # Don't pass differs/predicates as the only possible use case is to
        # use a different character differ within each line or predicates
        # for comparing lines
        d = diff_strings_linewise(a, b)
    else:
        raise RuntimeError("Can currently only diff list, dict, or str objects.")

    # We can turn this off for performance after the library has been well tested:
    validate_diff(d)

    return d


def diff_string_lines(a, b, path="", config=None):
    """Diff two lists of strings (lines)"""

    # This is mainly about short-circuiting to avoid full snakes for equal content
    # since we know we can rely on __eq__ comparison
    if len(a) == len(b) and a == b:
        return []
    
    return diff_strings_linewise(a, b)


def diff_sequence_multilevel(a, b, path="", config=None):
    """Compute diff of two lists with configurable behaviour."""

    if config is None:
        config = DiffConfig()

    # Invoke multilevel snake computation algorithm
    compares = config.predicates[path or '/']
    snakes = compute_snakes_multilevel(a, b, compares)

    # Convert snakes to diff
    return compute_diff_from_snakes(a, b, snakes, path=path, config=config)


def diff_lists(a, b, path="", config=None, shallow_diff=None):
    """Compute diff of two lists with configurable behaviour."""

    if config is None:
        config = DiffConfig()

    # If multiple compares are provided to this path, delegate to multilevel algorithm
    compares = config.predicates[path or '/']
    if len(compares) > 1:
        assert shallow_diff is None
        return diff_sequence_multilevel(a, b, path=path, config=config)

    # First make a shallow sequence diff with custom compare,
    # unless it's provided for us
    if shallow_diff is None:
        shallow_diff = diff_sequence(a, b, compares[0])

    # Next we recurse to diff items in sequence that are considered
    # similar by compares[0] in the loop below
    subpath = "/".join((path, "*"))
    diffit = config.differs[subpath]

    # Count consumed items i,j from a,b, (i="take" in patch_list)
    i, j = 0, 0
    di = SequenceDiffBuilder()
    M = len(shallow_diff)
    for ie in range(M+1):
        if ie < M:
            # Consume n more unmentioned items before this diff entry
            # Note that index can be larger than i in the case where items
            # have been deleted from a and then insertions from b occur.
            e = shallow_diff[ie]
            index = e.key
            n = max(0, index - i)
            askip, bskip = count_consumed_symbols(e)
        else:
            # Consume final items after the last diff entry
            e = None
            n = len(a) - i
            askip, bskip = 0, 0
            assert n >= 0, "Sanity check failed: Cannot have negative remaining entries"
            assert len(b) - j == n, "Sanity check failed: Base/remote indexing mismatch"

        # Recursively diff the n items that have been deemed similar
        for k in range(n):
            aval = a[i + k]
            bval = b[j + k]
            if not config.is_atomic(aval, subpath):
                cd = diffit(aval, bval, path=subpath, config=config)
                if cd:
                    di.patch(i + k, cd)  # FIXME: Not covered in tests, create test situation

        # Keep count of consumed items
        i += n + askip
        j += n + bskip

        # Insert the diff entry from shallow diff unless past the end
        # (this either adds or removes items)
        if ie < M:
            di.append(e)

    # Sanity check
    assert i == len(a), "Sanity check failed: Did not process all entries in a"
    assert j == len(b), "Sanity check failed: Did not process all entries in b"

    return di.validated()


def diff_dicts(a, b, path="", config=None):
    """Compute diff of two dicts with configurable behaviour.

    Keys in both a and b will be handled based on

    Make a one-level diff of dicts a and b, using given compare
    operator to specify which items are considered the same.

    Items not mentioned in diff are items where compare(x, y) return True.
    For other items the diff will contain delete, insert, or replace entries.
    """
    if config is None:
        config = DiffConfig()

    if not isinstance(a, dict) or not isinstance(b, dict):
        raise TypeError('Arguments to diff_dicts need to be dicts, got %r and %r' % (a, b))
    akeys = set(a.keys())
    bkeys = set(b.keys())

    di = MappingDiffBuilder()

    # Sorting keys in loops to get a deterministic diff result
    for key in sorted(akeys - bkeys):
        di.remove(key)

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]
        # If types are the same and nonatomic, recurse
        subpath = "/".join((path, key))
        if type(avalue) is type(bvalue) and not config.is_atomic(avalue, path=subpath):
            diffit = config.differs[subpath]
            dd = diffit(avalue, bvalue, path=subpath, config=config)
            if dd:
                di.patch(key, dd)
        else:
            if (path or '/') in config.predicates:
                # Could also this a warning, but I think it shouldn't be done
                raise RuntimeError(
                    "Found predicate(s) for path {} pointing to dict entry.".format(
                        path or '/'))
            if avalue != bvalue:
                di.replace(key, bvalue)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])

    return di.validated()
