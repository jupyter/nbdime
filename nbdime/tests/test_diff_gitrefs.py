
import os
import shutil
from itertools import zip_longest

import pytest

from git import InvalidGitRepositoryError

from ..gitfiles import changed_notebooks
from ..utils import EXPLICIT_MISSING_FILE


# Test that it can diff
#  - one ref
#  - two refs
#  - all of the above with a directory path
#  - all of the above with a filename path
#  - all of the above within a subdirectory of the repo
#  - all of the above with added and removed files in diff
#  - does not attempt to diff non-Notebook files
# Fails if:
#  - path is non-sensical
#  - path is not a git repo
#  - one or both references are invalid
#  - base ref is None


def _nb_name(f):
    if isinstance(f, str):
        return f
    return f.name


_filename = 'diff.ipynb'
_subdir_name = 'sub'
_subdir_filename = 'subfile.ipynb'
_subpath = os.path.join(_subdir_name, _subdir_filename)


# Test one/two args:

def test_head_vs_workdir(git_repo2):
    expected = [
        ('diff.ipynb (HEAD)', EXPLICIT_MISSING_FILE),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref(git_repo2):
    expected = [
        ('diff.ipynb (base)', 'diff.ipynb (local)'),
        ('sub/subfile.ipynb (base)', 'sub/subfile.ipynb (local)'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local'), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


# Test one/two args executed in subdir. Subdir should have no effect without `path` arg:

def test_head_vs_workdir_subdir(git_repo2):
    os.chdir(os.path.join(git_repo2, _subdir_name))
    expected = [
        ('diff.ipynb (HEAD)', EXPLICIT_MISSING_FILE),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref_subdir(git_repo2):
    os.chdir(os.path.join(git_repo2, _subdir_name))
    expected = [
        ('diff.ipynb (base)', 'diff.ipynb (local)'),
        ('sub/subfile.ipynb (base)', 'sub/subfile.ipynb (local)'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local'), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


# Test one/two args executed in subdir, with subdir relative path:

def test_head_vs_workdir_subdir_with_path(git_repo2, filespath):
    # Ensure diff for subfile:
    full_subfile_path = os.path.join(git_repo2, _subdir_name, 'subfile.ipynb')
    shutil.copy(os.path.join(filespath, 'foo--1.ipynb'),
                full_subfile_path)
    os.chdir(os.path.join(git_repo2, _subdir_name))
    expected = [
        ('sub/subfile.ipynb (HEAD)', 'sub/subfile.ipynb'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None, _subdir_filename), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref_subdir_with_path(git_repo2):
    os.chdir(os.path.join(git_repo2, _subdir_name))
    expected = [
        ('sub/subfile.ipynb (base)', 'sub/subfile.ipynb (local)'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local', _subdir_filename), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]



# Test one/two args with subdir path:

def test_head_vs_workdir_subdir_path(git_repo2):
    expected = [
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None, _subdir_name), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref_subdir_path(git_repo2):
    expected = [
        ('sub/subfile.ipynb (base)', 'sub/subfile.ipynb (local)'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local', _subdir_name), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


# Test one/two args with filename path:

def test_head_vs_workdir_filename(git_repo2):
    expected = [
        ('diff.ipynb (HEAD)', EXPLICIT_MISSING_FILE),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None, _filename), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref_filename(git_repo2):
    expected = [
        ('diff.ipynb (base)', 'diff.ipynb (local)'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local', _filename), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


# Test one/two args executed in subdir with filename path:

def test_head_vs_workdir_subdir_filename(git_repo2):
    expected = [
    ]
    os.chdir(os.path.join(git_repo2, _subdir_name))
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None, _subdir_filename), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref_subdir_filename(git_repo2):
    expected = [
        ('sub/subfile.ipynb (base)', 'sub/subfile.ipynb (local)'),
    ]
    os.chdir(os.path.join(git_repo2, _subdir_name))
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local', _subdir_filename), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


# Test one/two args with path to file in subdir:

def test_head_vs_workdir_subdir_filename_path(git_repo2):
    expected = [
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('HEAD', None, _subpath), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


def test_ref_vs_ref_subdir_filename_path(git_repo2):
    expected = [
        ('sub/subfile.ipynb (base)', 'sub/subfile.ipynb (local)'),
    ]
    for expected, actual in zip_longest(expected, changed_notebooks('base', 'local', _subpath), fillvalue=None):
        assert _nb_name(actual[0]) == expected[0]
        assert _nb_name(actual[1]) == expected[1]


# Test failure of one/two args with path to invalid file:

def test_head_vs_workdir_non_existant(git_repo2):
    assert 0 == len(tuple(changed_notebooks('HEAD', None, 'non-existant-file.ipynb')))


def test_ref_vs_ref_non_existant(git_repo2):
    assert 0 == len(tuple(changed_notebooks('base', 'local', 'non-existant-file.ipynb')))


# Test failure of one/two args with (invalid) path to file in parent directory:

def test_head_vs_workdir_invalid_path(git_repo2):
    os.chdir(os.path.join(git_repo2, _subdir_name))
    assert 0 == len(tuple(changed_notebooks('HEAD', None, _filename)))


def test_ref_vs_ref_invalid_path(git_repo2):
    os.chdir(os.path.join(git_repo2, _subdir_name))
    assert 0 == len(tuple(changed_notebooks('base', 'local', _filename)))


# Test failure for invalid directory path
def test_head_vs_workdir_invalid_subdir(git_repo2):
    assert 0 == len(tuple(changed_notebooks('HEAD', None, 'non-existant-dir')))


# Test failure outside git repo
def test_no_repo(tmpdir):
    tmpdir.chdir()
    with pytest.raises(InvalidGitRepositoryError):
        tuple(changed_notebooks('HEAD', None))
