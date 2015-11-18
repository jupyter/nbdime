# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""This file contains tests applying to reference notebook files from the nbdime/tests/files/ directory."""

from __future__ import print_function

import pytest
import copy

from nbdime import diff, patch
from nbdime.diff.diff_notebooks import diff_cells, patch_cells
from nbdime.diff.diff_notebooks import diff_notebooks, patch_notebook

# pytest conf.py stuff is tricky to use robustly, this works with no magic
from .fixtures import db, any_nb, any_nb_pair, assert_is_valid_notebook

def test_notebook_database_fixture(db):
    "Just test that the notebook file reader fixture is at least self-consistent."
    assert len(db) > 0
    assert len(list(db.keys())) == len(db)
    for name in db:
        assert name in db
        assert name + "notindb" not in db
        assert_is_valid_notebook(db[name])

def test_diff_and_patch_metadata_of_notebooks(any_nb_pair):
    "Test diff/patch on the metadata of any pair of notebooks in the test suite."
    nba, nbb = any_nb_pair
    a = nba["metadata"]
    b = nbb["metadata"]
    assert patch(a, diff(a, b)) == b

def test_diff_and_patch_notebooks_with_generic_diff(any_nb_pair):
    "Test generic diff/patch on any pair of notebooks in the test suite."
    a, b = any_nb_pair
    assert patch(a, diff(a, b)) == b

# Not yet implemented
@pytest.skip
def test_diff_and_patch_cells_of_notebooks(any_nb_pair):
    "Test diff/patch on the cells of any pair of notebooks in the test suite."
    nba, nbb = any_nb_pair
    a = nba["cells"]
    b = nbb["cells"]
    assert patch_cells(a, diff_cells(a, b)) == b

# Not yet implemented
@pytest.skip
def test_diff_and_patch_notebooks(any_nb_pair):
    "Test diff/patch on any pair of notebooks in the test suite."
    a, b = any_nb_pair
    assert patch_notebook(a, diff_notebooks(a, b)) == b
