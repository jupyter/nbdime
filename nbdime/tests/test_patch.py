# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from nbdime import patch


# TODO: Check and improve test coverage
# TODO: Add tests for invalid input and error handling
# TODO: Add more corner cases (combinations of delete-then-add etc.)


def test_patch_str():
    # Test +, single item insertion
    assert patch("42", [["+", 0, "3"], ["-", 1]]) == "34"

    # Test -, single item deletion
    assert patch("3", [["-", 0]]) == ""
    assert patch("42", [["-", 0]]) == "2"
    assert patch("425", [["-", 0]]) == "25"
    assert patch("425", [["-", 1]]) == "45"
    assert patch("425", [["-", 2]]) == "42"

    # Test :, single item replace
    assert patch("52", [[":", 0, "4"]]) == "42"
    assert patch("41", [[":", 1, "2"]]) == "42"
    assert patch("42", [[":", 0, "3"], [":", 1, "5"]]) == "35"
    assert patch("hello", [[":", 0, "H"]]) == "Hello"
    # Replace by delete-then-insert
    assert patch("world", [["-", 0], ["+", 0, "W"]]) == "World"

    # Test !, item patch (doesn't make sense for str)
    pass

    # Test ++, sequence insertion
    assert patch("", [["++", 0, "34"], ["+", 0, "5"], ["++", 0, "67"]]) == "34567"

    # Test --, sequence deletion
    assert patch("abcd", [["--", 0, 2]]) == "cd"
    assert patch("abcd", [["--", 1, 2]]) == "ad"
    assert patch("abcd", [["--", 2, 2]]) == "ab"

    # Test ::, sequence replace
    assert patch("abc", [["::", 0, "fg"]]) == "fgc"
    assert patch("abc", [["::", 1, "fg"]]) == "afg"
    assert patch("abc", [["::", 0, "fgh"]]) == "fgh"

def test_patch_list():
    # Test +, single item insertion
    assert patch([], [["+", 0, 3]]) == [3]
    assert patch([], [["+", 0, 3], ["+", 0, 4]]) == [3, 4]
    assert patch([], [["+", 0, 3], ["+", 0, 4], ["+", 0, 5]]) == [3, 4, 5]

    # Test -, single item deletion
    assert patch([3], [["-", 0]]) == []
    assert patch([5, 6, 7], [["-", 0]]) == [6, 7]
    assert patch([5, 6, 7], [["-", 1]]) == [5, 7]
    assert patch([5, 6, 7], [["-", 2]]) == [5, 6]
    assert patch([5, 6, 7], [["-", 0], ["-", 2]]) == [6]

    # Test :, single item replace
    pass

    # Test !, item patch
    assert patch(["hello", "world"], [["!", 0, [[":", 0, "H"]]], ["!", 1, [["-", 0], ["+", 0, "W"]]]]) == ["Hello", "World"]

    # Test ++, sequence insertion
    assert patch([], [["++", 0, [3,4]], ["+", 0, 5], ["++", 0, [6,7]]]) == [3, 4, 5, 6, 7]

    # Test --, sequence deletion
    assert patch([5, 6, 7, 8], [["--", 0, 2]]) == [7, 8]
    assert patch([5, 6, 7, 8], [["--", 1, 2]]) == [5, 8]
    assert patch([5, 6, 7, 8], [["--", 2, 2]]) == [5, 6]

    # Test ::, sequence replace
    assert patch(["a", "b", "c"], [["::", 0, ["f", "g"]]]) == ["f", "g", "c"]
    assert patch(["a", "b", "c"], [["::", 1, ["f", "g"]]]) == ["a", "f", "g"]
    assert patch(["a", "b", "c"], [["::", 0, ["f", "g", "h"]]]) == ["f", "g", "h"]

def test_patch_dict():
    # Test +, single item insertion
    assert patch({}, [["+", "d", 4]]) == {"d": 4}
    assert patch({"a": 1}, [["+", "d", 4]]) == {"a": 1, "d": 4}

    #assert patch({"d": 1}, [["+", "d", 4]]) == {"d": 4} # currently triggers assert, raise exception or allow?

    # Test -, single item deletion
    assert patch({"a": 1}, [["-", "a"]]) == {}
    assert patch({"a": 1, "b": 2}, [["-", "a"]]) == {"b": 2}

    # Test :, single item replace
    assert patch({"a": 1, "b": 2}, [[":", "a", 3]]) == {"a": 3, "b": 2}
    assert patch({"a": 1, "b": 2}, [[":", "a", 3], [":", "b", 5]]) == {"a": 3, "b": 5}

    # Test !, item patch
    subdiff = [["!", 0, [[":", 0, "H"]]], ["!", 1, [["-", 0], ["+", 0, "W"]]]]
    assert patch({"a": ["hello", "world"], "b": 3}, [["!", "a", subdiff]]) == {"a": ["Hello", "World"], "b": 3}
