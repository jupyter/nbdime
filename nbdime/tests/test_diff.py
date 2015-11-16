
from nbdime.diff.diff import diff
from nbdime.diff.validation import is_valid_diff
from nbdime.diff.patch import patch

def test_generic_diff():
    a = []
    b = []
    d = diff(a, b)
    assert is_valid_diff(d)
    assert patch(a, d) == b
