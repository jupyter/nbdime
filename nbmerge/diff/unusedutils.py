"""Utilities currently unused, written during some experimentation. Delete if they stay unused."""

def iter_dict_paths(obj, basepath=()):
    """Iterate over all paths of nested dicts.

    Yields paths, each a list of keys into nested dicts.
    """
    assert isinstance(obj, dict)
    for k, v in obj.items():
        p = basepath + (k,)
        if isinstance(v, dict):
            for pp in iter_dict_paths(v, p):
                yield pp
        else:
            yield p

def deep_dict_items(obj, basepath=()):
    """Iterate over deep items in nested dict.

    Yields (path, value) with path being list of keys into nested dicts.
    """
    assert isinstance(obj, dict)
    basepath = tuple(basepath)
    for k, v in obj.items():
        p = basepath + (k,)
        if isinstance(v, dict):
            for pp, u in deep_dict_items(v, p):
                yield pp, u
        else:
            yield list(p), v

def sorted_dict_paths(obj, basepath=()):
    """Iterate over all paths of nested dicts, sorted.

    Yields paths, each a list of keys into nested dicts.
    """
    assert isinstance(obj, dict)
    for k in sorted(obj):
        v = obj[k]
        p = basepath + (k,)
        if isinstance(v, dict):
            for pp in sorted_dict_paths(v, p):
                yield pp
        else:
            yield p



import Levenshtein

def str_distance(str1, str2):
    """Return a measure of the distance between two string.

    The return value is a number between 0.0 and 1.0 where 0.0 means equal.
    """
    # Cutoff because Levenshtein is slow
    if str1 == str2:
        return 0.0
    return 1.0 - Levenshtein.ratio(str1, str2)
