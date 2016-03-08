# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

#from six.moves import xrange as range

#import copy
#import pytest

from nbdime import merge_notebooks

from .fixtures import sources_to_notebook


# FIXME: Extend tests to more merge situations!


def test_merge_cell_sources_neighbouring_inserts():
    base = [[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    local = [[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    remote = [[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(7))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    expected = sources_to_notebook([[
        "def f(x):",
        "    return x**2",
        ], [
        "print(f(3))",
        ], [
        "print(f(7))",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ])
    args = None
    actual, lco, rco = merge_notebooks(sources_to_notebook(base), sources_to_notebook(local), sources_to_notebook(remote), args)
    assert not lco
    assert not rco
    assert actual == expected


def test_merge_cell_sources_separate_inserts():
    base = [[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    local = [[
        "print(f(3))",
        ], [
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ],
        ]
    remote = [[
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ]
    expected = sources_to_notebook([[
        "print(f(3))",
        ], [
        "def f(x):",
        "    return x**2",
        ], [
        "def g(y):",
        "    return y + 2",
        ], [
        "print(f(7))",
        ],
        ])
    args = None
    actual, lco, rco = merge_notebooks(sources_to_notebook(base), sources_to_notebook(local), sources_to_notebook(remote), args)
    assert not lco
    assert not rco
    assert actual == expected
