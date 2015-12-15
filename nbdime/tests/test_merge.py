from nbdime import merge


def test_shallow_merge_dicts_delete():
    # local removes an entry
    b = {"b": 1, "a": 3}
    l = {"b": 1}
    r = {"b": 1, "a": 3}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1}
    assert lc == {}
    assert rc == {}

    # remote removes an entry
    b = {"b": 1, "a": 3}
    l = {"b": 1, "a": 3}
    r = {"b": 1}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1}
    assert lc == {}
    assert rc == {}

    # both remove the same entry
    b = {"b": 1, "a": 3}
    l = {"b": 1}
    r = {"b": 1}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1}
    assert lc == {}
    assert rc == {}


def test_shallow_merge_dicts_insert():
    # local adds an entry
    b = {"b": 1}
    l = {"b": 1, "l": 2}
    r = {"b": 1}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "l": 2}
    assert lc == {}
    assert rc == {}

    # remote adds an entry
    b = {"b": 1}
    l = {"b": 1}
    r = {"b": 1, "r": 3}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "r": 3}
    assert lc == {}
    assert rc == {}

    # local and remote adds an entry each
    b = {"b": 1}
    l = {"b": 1, "l": 2}
    r = {"b": 1, "r": 3}
    m, lc, rc = merge(b, l, r)
    assert m == {"b": 1, "l": 2, "r": 3}
    assert lc == {}
    assert rc == {}


def test_deep_merge_dicts_delete():
    # local removes an entry
    b = {"p": {"b": 1, "a": 3}}
    l = {"p": {"b": 1}}
    r = {"p": {"b": 1, "a": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == {}
    assert rc == {}

    # remote removes an entry
    b = {"p": {"b": 1, "a": 3}}
    l = {"p": {"b": 1, "a": 3}}
    r = {"p": {"b": 1}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == {}
    assert rc == {}

    # both remove the same entry
    b = {"p": {"b": 1, "a": 3}}
    l = {"p": {"b": 1}}
    r = {"p": {"b": 1}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1}}
    assert lc == {}
    assert rc == {}


def test_deep_merge_dicts_insert():
    # local adds an entry
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1, "l": 2}}
    r = {"p": {"b": 1}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "l": 2}}
    assert lc == {}
    assert rc == {}

    # remote adds an entry
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1}}
    r = {"p": {"b": 1, "r": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "r": 3}}
    assert lc == {}
    assert rc == {}

    # local and remote adds an entry each
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1, "l": 2}}
    r = {"p": {"b": 1, "r": 3}}
    m, lc, rc = merge(b, l, r)
    assert m == {"p": {"b": 1, "l": 2, "r": 3}}
    assert lc == {}
    assert rc == {}


def test_merge_nonconflicting_nested_dicts():
    # local and remote each adds, deletes, and modifies entries inside nested structure without conflicts
    b = {"a": {}, "d": {"x": 4, "y": 5, "z": 6}, "m": {"x": 7, "y": 8, "z": 9}}
    l = {"a": {"x": 1, "y": 2}, "d": {"z": 6}, "m": {"x": 17, "y": 18, "z": 9}}
    r = {"a": {"x": 1, "z": 3}, "d": {"y": 5}, "m": {"x": 17, "y": 8, "z": 19}}
    m, lc, rc = merge(b, l, r)
    assert m == {"a": {"x": 1, "y": 2, "z": 3}, "d": {}, "m": {"x": 17, "y": 18, "z": 19}}
    assert lc == {}
    assert rc == {}


def test_merge_conflicting_nested_dicts():
    # local and remote each adds, deletes, and modifies entries inside nested structure with everything conflicting
    b = {"a": {"x": 1},         "d": {"x": 4, "y": 5}, "m": {"x": 7}}
    l = {"a": {"x": 2, "y": 4}, "d": {        "y": 6}, "m": {"x": 17}, "n": {"q": 9}}
    r = {"a": {"x": 3, "y": 5}, "d": {"x": 5},         "m": {"x": 27}, "n": {"q": 19}}
    m, lc, rc = merge(b, l, r)
    assert m == {"a": {}, "d": {}, "m": {}, "n": {}}
    assert lc == {"a": ["!", {"x": [":", 2], "y": ["+", 4]}],
                  "d": ["!", {"x": ["-"], "y": [":", 6]}],
                  "m": ["!", {"x": [":", 17]}],
                  "n": ["!", {"q": ["+", 9]}],
                  }
    assert rc == {"a": ["!", {"x": [":", 3], "y": ["+", 5]}],
                  "d": ["!", {"x": [":", 5], "y": ["-"]}],
                  "m": ["!", {"x": [":", 27]}],
                  "n": ["!", {"q": ["+", 19]}],
                 }
    #assert c == {"a": {"x": [1, 2, 3], "y": [None, 4, 5]}, "d": {"x": [4, None, 5], "y": [5, 6, None]},
    #             "m": {"x": [7, 17, 27]}}
