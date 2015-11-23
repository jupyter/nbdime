# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import pytest
import os
import glob
import nbformat

from nbdime import patch, shallow_diff, deep_diff
from nbdime.dformat import is_valid_diff

def testspath():
    return os.path.abspath(os.path.dirname(__file__))

def filespath():
    return os.path.join(testspath(), "files")

class NBTestDataBase(object):
    def __init__(self):
        #self.testspath = testspath()
        self.filespath = filespath()
        self.cache = {}
        filenames = glob.glob(os.path.join(self.filespath, "*.ipynb"))
        names = [os.path.basename(fn).replace(".ipynb", "") for fn in filenames]
        self.names = list(sorted(names))

    def __len__(self):
        return len(self.names)

    def __iter__(self):
        return self.keys()

    def __hasitem__(self, name):
        return name in self.names

    def keys(self):
        return iter(self.names)

    def values(self):
        return (self[name] for name in self.names)

    def items(self):
        return ((name, self[name]) for name in self.names)

    def __getitem__(self, name):
        if isinstance(name, int):
            name = self.names[name]
        # Cache file reads
        nbs = self.cache.get(name)
        if nbs is None:
            with open(os.path.join(self.filespath, name + ".ipynb")) as f:
                nbs = f.read()
            self.cache[name] = nbs
        # But return a new notebook copy every time
        return nbformat.reads(nbs, as_version=4)

_db = NBTestDataBase()

@pytest.fixture
def db():
    return _db

@pytest.fixture(params=range(len(_db)))
def any_nb(request):
    return _db[request.param]

@pytest.fixture(params=range(len(_db)**2))
def any_nb_pair(request):
    return (_db[request.param // len(_db)], _db[request.param % len(_db)])

def assert_is_valid_notebook(nb):
    """These are the current assumptions on notebooks in these tests. Loosen on demand."""
    assert nb["nbformat"] == 4
    assert nb["nbformat_minor"] == 0
    assert isinstance(nb["metadata"], dict)
    assert isinstance(nb["cells"], list)
    assert all(isinstance(cell, dict) for cell in nb["cells"])


def check_diff_and_patch(a, b):
    "Check that patch(a, diff(a,b)) reproduces b."
    d = shallow_diff(a, b)
    assert is_valid_diff(d)
    assert patch(a, d) == b

    d = deep_diff(a, b)
    assert is_valid_diff(d)
    assert patch(a, d) == b

def check_symmetric_diff_and_patch(a, b):
    "Check that patch(a, diff(a,b)) reproduces b and vice versa."
    check_diff_and_patch(a, b)
    check_diff_and_patch(b, a)
