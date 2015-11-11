
import copy

from .validation import validate_diff
from .diff_sequence import diff_sequence

__all__ = ["diff"]

def diff_lists(a, b):
    assert isinstance(a, list) and isinstance(b, list)
    # TODO: For now, only lists of atomic values are supported. Fix on demand.
    assert not any(isinstance(x, (list, dict)) for x in a)
    assert not any(isinstance(x, (list, dict)) for x in b)
    return diff_sequence(a, b)

def diff_strings(a, b):
    # TODO: I think this should work...
    return diff_lists(list(a), list(b))

# Using this sentinel instead of None to allow the value None
_missing_sentinel = object()
def diff_dicts(a, b):
    assert isinstance(a, dict) and isinstance(b, dict)
    d = []

    # Sort keys to get a deterministic diff result
    akeys = sorted(a.keys())
    bkeys = sorted(b.keys())
    for key in akeys:
        avalue = a[key]
        bvalue = b.get(key, _missing_sentinel)
        if bvalue is _missing_sentinel:
            # key is not in b, deleting avalue
            d.append(['-', key])
        else:
            # key is in both
            if ((isinstance(avalue, dict) and isinstance(bvalue, dict))
                or (isinstance(avalue, list) and isinstance(bvalue, list))):
                # diff subdicts or sublists recursively and add patch entry if subdiff is not empty
                subdiff = diff_dicts(avalue, bvalue)
                if subdiff:
                    d.append(["!", key, subdiff])
            elif avalue != bvalue:
                # values are different, so we replace old with new
                # TODO: When we add more type knowledge, may need to rethink this a bit.
                d.append([':', key, bvalue])

    for key in bkeys:
        bvalue = b[key]
        avalue = a.get(key, _missing_sentinel)
        if avalue is _missing_sentinel:
            # key is not in a, adding bvalue
            d.append(['+', key, bvalue])
    return d

def diff(a, b):
    if isinstance(a, list) and isinstance(b, list):
        d = diff_lists(a, b)
    elif isinstance(a, dict) and isinstance(b, dict):
        d = diff_dicts(a, b)
    elif isinstance(a, basestring) and isinstance(b, basestring):
        d = diff_strings(a, b)
    else:
        raise RuntimeError("Can currently only diff list, dict, or str objects.")
    validate_diff(d)
    return d
