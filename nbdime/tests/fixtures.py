# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function
from six.moves import xrange as range

import pytest
import os
import glob
import nbformat
import re

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

        r = re.compile("^(.*)-([0-9]+)$")
        matches = [r.match(name) for name in self.names]
        self.groups = { basename: [name for name in self.names if name.startswith(basename)]
                        for basename in set(m.groups()[0] for m in matches if m) }

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


def _any_nb_name():
    return _db.names

def _any_nb_pair_names():
    pairs = []
    names = _db.names
    for i in range(len(names)):
        for j in range(len(names)):
            pairs.append((names[i], names[j]))
    return pairs

def _matching_nb_pair_names():
    pairs = []
    for basename, names in sorted(_db.groups.items()):
        for i in range(len(names)):
            for j in range(len(names)):
                pairs.append((names[i], names[j]))
    return pairs


@pytest.fixture
def db():
    return _db

@pytest.fixture(params=_any_nb_name())
def any_nb(request):
    return _db[request.param]

@pytest.fixture(params=_any_nb_pair_names())
def any_nb_pair(request):
    a, b = request.param
    return _db[a], _db[b]

@pytest.fixture(params=_matching_nb_pair_names())
def matching_nb_pairs(request):
    a, b = request.param
    return _db[a], _db[b]


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
