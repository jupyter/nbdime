
"""This file defines (fairly) generic diff/patch functions for json-ish data.

Generic diff format
===================
The diff of two objects is a list of transformations.

Each transformation has the format:

   [action, path[, value|diff]]

Action can be one of

    * "-": delete value at path
    * "+": insert value at path (if path is list index, 'at' means just before the item at that index)
    * "!": patch value at path with diff

Examples:

   ["-", path]
   ["+", path, newvalue]
   ["!", path, diff]

The path is a list of keys into nested dicts.

Value can be omitted for "-".
"""


"""
Subdiff paths are relative to the object in a[path], i.e.
    patch(a, diff) -> a[path] = patch(a[path], subdiff)

diff = [
    ["-", path],
    ["+", path, value],
    ["!", path, subdiff],
    ]

If the object is a list,

assert diff([], {}) == [
    ["-", None],
    ["+", None, {}]
    ]

assert diff([1], []) == [
    ["-", 0],
    ]

assert diff([], [1]) == [
    ["+", 0, 1],
    ]

assert diff([1, 2], [1]) == [
    ["-", 1],
    ]

assert diff([1], [1, 2]) == [
    ["+", 1, 2],
    ]

"""
