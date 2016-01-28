
from nbdime.utils import strings_to_lists, revert_strings_to_lists

def test_string_to_lists():
    obj = {"c": [{"s": "ting\ntang", "o": [{"ot": "stream"}]}]}
    obj2 = strings_to_lists(obj)
    obj3 = revert_strings_to_lists(obj2)
    assert obj3 == obj
