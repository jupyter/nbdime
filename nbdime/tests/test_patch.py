# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from nbdime import patch
from nbdime.dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE


# TODO: Check and improve test coverage
# TODO: Add tests for invalid input and error handling
# TODO: Add more corner cases (combinations of delete-then-add etc.)


def test_patch_str():
    # Test +, single item insertion
    assert patch("42", [[INSERT, 0, "3"], [DELETE, 1]]) == "34"

    # Test -, single item deletion
    assert patch("3", [[DELETE, 0]]) == ""
    assert patch("42", [[DELETE, 0]]) == "2"
    assert patch("425", [[DELETE, 0]]) == "25"
    assert patch("425", [[DELETE, 1]]) == "45"
    assert patch("425", [[DELETE, 2]]) == "42"

    # Test :, single item replace
    assert patch("52", [[REPLACE, 0, "4"]]) == "42"
    assert patch("41", [[REPLACE, 1, "2"]]) == "42"
    assert patch("42", [[REPLACE, 0, "3"], [REPLACE, 1, "5"]]) == "35"
    assert patch("hello", [[REPLACE, 0, "H"]]) == "Hello"
    # Replace by delete-then-insert
    assert patch("world", [[DELETE, 0], [INSERT, 0, "W"]]) == "World"

    # Test !, item patch (doesn't make sense for str)
    pass

    # Test ++, sequence insertion
    assert patch("", [[SEQINSERT, 0, "34"], [INSERT, 0, "5"], [SEQINSERT, 0, "67"]]) == "34567"

    # Test --, sequence deletion
    assert patch("abcd", [[SEQDELETE, 0, 2]]) == "cd"
    assert patch("abcd", [[SEQDELETE, 1, 2]]) == "ad"
    assert patch("abcd", [[SEQDELETE, 2, 2]]) == "ab"

def test_patch_list():
    # Test +, single item insertion
    assert patch([], [[INSERT, 0, 3]]) == [3]
    assert patch([], [[INSERT, 0, 3], [INSERT, 0, 4]]) == [3, 4]
    assert patch([], [[INSERT, 0, 3], [INSERT, 0, 4], [INSERT, 0, 5]]) == [3, 4, 5]

    # Test -, single item deletion
    assert patch([3], [[DELETE, 0]]) == []
    assert patch([5, 6, 7], [[DELETE, 0]]) == [6, 7]
    assert patch([5, 6, 7], [[DELETE, 1]]) == [5, 7]
    assert patch([5, 6, 7], [[DELETE, 2]]) == [5, 6]
    assert patch([5, 6, 7], [[DELETE, 0], [DELETE, 2]]) == [6]

    # Test :, single item replace
    pass

    # Test !, item patch
    assert patch(["hello", "world"], [[PATCH, 0, [[REPLACE, 0, "H"]]], [PATCH, 1, [[DELETE, 0], [INSERT, 0, "W"]]]]) == ["Hello", "World"]

    # Test ++, sequence insertion
    assert patch([], [[SEQINSERT, 0, [3,4]], [INSERT, 0, 5], [SEQINSERT, 0, [6,7]]]) == [3, 4, 5, 6, 7]

    # Test --, sequence deletion
    assert patch([5, 6, 7, 8], [[SEQDELETE, 0, 2]]) == [7, 8]
    assert patch([5, 6, 7, 8], [[SEQDELETE, 1, 2]]) == [5, 8]
    assert patch([5, 6, 7, 8], [[SEQDELETE, 2, 2]]) == [5, 6]

def test_patch_dict():
    # Test +, single item insertion
    assert patch({}, [[INSERT, "d", 4]]) == {"d": 4}
    assert patch({"a": 1}, [[INSERT, "d", 4]]) == {"a": 1, "d": 4}

    #assert patch({"d": 1}, [[INSERT, "d", 4]]) == {"d": 4} # currently triggers assert, raise exception or allow?

    # Test -, single item deletion
    assert patch({"a": 1}, [[DELETE, "a"]]) == {}
    assert patch({"a": 1, "b": 2}, [[DELETE, "a"]]) == {"b": 2}

    # Test :, single item replace
    assert patch({"a": 1, "b": 2}, [[REPLACE, "a", 3]]) == {"a": 3, "b": 2}
    assert patch({"a": 1, "b": 2}, [[REPLACE, "a", 3], [REPLACE, "b", 5]]) == {"a": 3, "b": 5}

    # Test !, item patch
    subdiff = [[PATCH, 0, [[REPLACE, 0, "H"]]], [PATCH, 1, [[DELETE, 0], [INSERT, 0, "W"]]]]
    assert patch({"a": ["hello", "world"], "b": 3}, [[PATCH, "a", subdiff]]) == {"a": ["Hello", "World"], "b": 3}
