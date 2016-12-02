# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from six import string_types

from contextlib import contextmanager
import io
import glob
import os
import re
import shlex
import sys
from subprocess import check_output, check_call, STDOUT

import pytest
import nbformat

from nbdime import patch, diff
from nbdime.diff_format import is_valid_diff


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

        # Build groups on the form {basename: [list of names 'basename--subname']},
        r = re.compile("^(.*)--(.*)$")
        matches = [r.match(name) for name in self.names]
        basenames = set(m.groups()[0] for m in matches if m)
        self.groups = {basename: [name for name in self.names if name.startswith(basename)]
                       for basename in basenames}

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
            fn = os.path.join(self.filespath, name + ".ipynb")
            with io.open(fn, encoding="utf8") as f:
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
        for j in range(i, len(names)):
            pairs.append((names[i], names[j]))
    return pairs


def _matching_nb_pair_names():
    pairs = []
    for basename, names in sorted(_db.groups.items()):
        for i in range(len(names)):
            for j in range(i, len(names)):
                pairs.append((names[i], names[j]))
    return pairs


def _matching_nb_triplet_names():
    triplets = []
    for basename, names in sorted(_db.groups.items()):
        if basename in _db.names:
            for i in range(len(names)):
                for j in range(i, len(names)):
                    triplets.append((basename, names[i], names[j]))
    return triplets


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


@pytest.fixture(params=_matching_nb_triplet_names())
def matching_nb_triplets(request):
    a, b, c = request.param
    print(a, b, c)
    return _db[a], _db[b], _db[c]


def assert_is_valid_notebook(nb):
    """These are the current assumptions on notebooks in these tests. Loosen on demand."""
    assert nb["nbformat"] == 4
    #assert nb["nbformat_minor"] == 0
    assert isinstance(nb["metadata"], dict)
    assert isinstance(nb["cells"], list)
    assert all(isinstance(cell, dict) for cell in nb["cells"])


def check_diff_and_patch(a, b):
    "Check that patch(a, diff(a,b)) reproduces b."
    d = diff(a, b)
    assert is_valid_diff(d)
    assert patch(a, d) == b


def check_symmetric_diff_and_patch(a, b):
    "Check that patch(a, diff(a,b)) reproduces b and vice versa."
    check_diff_and_patch(a, b)
    check_diff_and_patch(b, a)


def sources_to_notebook(sources):
    assert isinstance(sources, list)
    assert len(sources) == 0 or isinstance(sources[0], list)
    nb = nbformat.v4.new_notebook()
    for source in sources:
        if isinstance(source, list):
            source = "".join(source)
        nb.cells.append(nbformat.v4.new_code_cell(source))
    return nb


def notebook_to_sources(nb, as_str=True):
    sources = []
    for cell in nb["cells"]:
        source = cell["source"]
        if as_str and isinstance(source, list):
            source = "\n".join([line.strip("\n") for line in source])
        elif not as_str and isinstance(source, string_types):
            source = source.splitlines(True)
        sources.append(source)
    return sources


def outputs_to_notebook(outputs):
    assert isinstance(outputs, list)
    assert len(outputs) == 0 or isinstance(outputs[0], list)
    nb = nbformat.v4.new_notebook()
    for cell_outputs in outputs:
        cell = nbformat.v4.new_code_cell()
        nb.cells.append(cell)
        for output in cell_outputs:
            if isinstance(output, string_types):
                output = nbformat.v4.new_output(
                    output_type="display_data",
                    data={
                        "text/plain": output,
                    }
                )
            assert isinstance(output, dict)
            cell.outputs.append(output)
    return nb


@contextmanager
def assert_clean_exit():
    """Assert that SystemExit is called with code=0"""
    with pytest.raises(SystemExit) as e:
        yield
    assert e.value.code == 0


def call(cmd):
    """Call a command
    
    if str, split into command list
    """
    if isinstance(cmd, string_types):
        cmd = shlex.split(cmd)
    return check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)


def get_output(cmd, err=False):
    """Run a command and get its output (as text)"""
    if isinstance(cmd, string_types):
        cmd = shlex.split(cmd)
    stderr = STDOUT if err else sys.stderr
    return check_output(cmd, stderr=stderr).decode('utf8', 'replace')
