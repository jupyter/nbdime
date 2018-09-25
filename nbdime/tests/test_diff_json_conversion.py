
import pytest
import json
from nbdime import diff
from nbdime.diff_utils import to_clean_dicts, to_json_patch

def test_diff_to_json():
    a = { "foo": [1,2,3], "bar": {"ting": 7, "tang": 123 } }
    b = { "foo": [1,3,4], "bar": {"tang": 126, "hello": "world" } }
    d1 = diff(a, b)

    d2 = to_clean_dicts(d1)
    assert len(d2) == len(d1)
    assert all(len(e2) == len(e1) for e1, e2 in zip(d1, d2))

    j = json.dumps(d1)
    d3 = json.loads(j)
    assert len(d3) == len(d1)
    assert all(len(e3) == len(e1) for e1, e3 in zip(d1, d3))
    assert d2 == d3


def test_diff_to_json_patch():
    a = [2, 3, 4]
    b = [1, 2, 4, 6]
    d = diff(a, b)

    assert to_json_patch(d) == [
        {'op': 'add', 'path': '/0', 'value': 1},
        {'op': 'remove', 'path': '/2'},
        {'op': 'add', 'path': '/3', 'value': 6}
        ]

    try:
        import jsonpatch
    except ImportError:
        jsonpatch = None
        pytest.xfail("Not comparing to jsonpatch")

    if jsonpatch:
        assert to_json_patch(d) == jsonpatch.make_patch(a, b).patch
