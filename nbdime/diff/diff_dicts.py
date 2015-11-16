
__all__ = ["diff_nested_dicts", "patch_nested_dicts"]

import copy

def get_known_dict_path(d, path):
    "Return d[path[0]][path[1]][...], assuming path exists."
    for key in path:
        d = d[key]
    return d

def get_dict_path(d, path, missing=None):
    "Return d[path[0]][path[1]][...], returning missing object if path is missing."
    for key in path:
        d = d.get(key, missing)
        if d is missing:
            break
    return d

def add_dict_path(d, path):
    "Return d[path[0]][path[1]][...], adding any missing subdicts."
    for key in path:
        sub = d.get(key)
        if sub is None:
            sub = {}
            d[key] = sub
        else:
            assert isinstance(sub, dict)
        d = sub
    return d

_missing_sentinel = object()
def diff_nested_dicts(a, b, basepath=()):
    """Diff dicts of dicts, treating anything not a dict as an atomic value. Compatible with patch_nested_dicts."""
    assert isinstance(a, dict) and isinstance(b, dict)
    diff = []
    akeys = sorted(a.keys())
    bkeys = sorted(b.keys())
    for k in akeys:
        path = basepath + (k,)
        avalue = a[k]
        bvalue = b.get(k, _missing_sentinel)
        if bvalue is _missing_sentinel:
            # path is not in b, deleting avalue (could be entire subdict)
            diff.append(['-', list(path)])
        else:
            # path is in both
            if isinstance(avalue, dict) and isinstance(bvalue, dict):
                # diff subdicts recursively, note the passing of basepath=path
                diff += diff_nested_dicts(avalue, bvalue, path)
            else:
                # values have different types, replace old with new
                # (at this point avalue/bvalue could be compared
                # and further diffed if more types were supported)
                diff.append(['!', list(path), bvalue])
    for k in bkeys:
        bvalue = b[k]
        avalue = a.get(k, _missing_sentinel)
        if avalue is _missing_sentinel:
            path = basepath + (k,)
            # path is not in a, adding bvalue (could be entire subdict)
            diff.append(['+', list(path), bvalue])
    return diff

def patch_nested_dicts(md, diff):
    """Patch dicts of dicts with diff produced by diff_nested_dicts."""
    md = copy.deepcopy(md)
    for t in diff:
        act = t[0]
        path = t[1]
        if act == '-':
            d = get_known_dict_path(md, path[:-1])
            del d[path[-1]]
        elif act == '+':
            d = add_dict_path(md, path[:-1])
            d[path[-1]] = t[2]
        elif act == '!':
            d = get_known_dict_path(md, path[:-1])
            d[path[-1]] = t[2]
    return md
