#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import io
from collections import deque

from six import string_types

os.environ['GIT_PYTHON_REFRESH'] = 'quiet'
from git import Repo, InvalidGitRepositoryError, BadName, NoSuchPathError

from .utils import EXPLICIT_MISSING_FILE, pushd


class BlobWrapper(io.StringIO):
    """StringIO with a name attribute"""
    name = ''


def get_repo(path):
    """Gets a Repo for path, also if path is a subdirectory of a repository

    Returns a tuple with the Repo object, and a list of subdirectories
    between path and the parent repository"""
    path = os.path.realpath(os.path.abspath(path))
    popped = deque()
    while True:
        try:
            repo = Repo(path)
            return (repo, tuple(popped))
        except (InvalidGitRepositoryError, NoSuchPathError):
            path, pop = os.path.split(path)
            if not pop:
                raise
            popped.appendleft(pop)


def find_repo_root(path):
    """Gets the directory containing the working tree"""
    repo = get_repo(path)[0]
    return repo.working_tree_dir


def traverse_tree(tree, subdirs):
    """Get the subtree according to given list of subdirectories"""
    if len(subdirs) == 0:
        return tree
    sub = subdirs[0]
    # Find first subtree whose name matches sub:
    subtree = next((st for st in tree.trees if st.name == sub), None)
    if subtree is None:
        raise KeyError('%s is not a subtree of %s' % (sub, tree.name))
    return traverse_tree(subtree, subdirs[1:])


def is_gitref(candidate):
    """Is candidate a gitref, or is it a file/filename?

    Returns false for collisions (e.g. when it is both a valid filename and gitref).
    Tests relative to current directory.
    """
    return (
        (candidate is None or not os.path.exists(candidate)) and
        candidate != EXPLICIT_MISSING_FILE and
        is_valid_gitref(candidate)
        )


def is_valid_gitref(ref, path=None):
    """Checks whether ref is a valid gitref in `path`, per git-rev-parse
    """
    try:
        repo = get_repo(path or os.curdir)[0]
        repo.commit(ref)
        return True
    except InvalidGitRepositoryError:
        return False
    except BadName:
        return False


def is_path_in_repo(path):
    """Checks whether path is part of a git repository"""
    try:
        get_repo(path)
        return True
    except InvalidGitRepositoryError:
        return False


def _get_diff_entry_stream(path, blob, ref_name, repo_dir):
    """Get a stream to the notebook, for a given diff entry's path and blob

    Returns None if path is not a Notebook file, and EXPLICIT_MISSING_FILE
    if path is missing."""
    if path:
        if not path.endswith('.ipynb'):
            return None
        if blob is None:
            # Diffing against working copy, use file on disk!
            with pushd(repo_dir):
                try:
                    return io.open(path)
                except IOError:
                    return EXPLICIT_MISSING_FILE
        else:
            # There were strange issues with passing blob data_streams around,
            # so we solve this by reading into a StringIO buffer.
            # The penalty should be low as long as changed_notebooks are used
            # properly as an iterator.
            f = BlobWrapper(blob.data_stream.read().decode('utf-8'))
            f.name = '%s (%s)' % (path, ref_name)
            return f
    return EXPLICIT_MISSING_FILE


def changed_notebooks(ref_base, ref_remote, paths=None, repo_dir=None):
    """Iterator over all notebooks in path that has changed between the two git refs

    References are all valid values according to git-rev-parse. If ref_remote
    is None, the difference is taken between ref_base and the working directory.
    Iterator value is a base/remote pair of streams to Notebooks
    (or possibly EXPLICIT_MISSING_FILE for added/removed files).
    """
    repo, popped = get_repo(repo_dir or os.curdir)
    if repo_dir is None:
        repo_dir = os.path.relpath(repo.working_tree_dir, os.curdir)
    if isinstance(paths, string_types):
        paths = (paths,)
    if paths and popped:
        # All paths need to be prepended by popped
        paths = [os.path.join(*(popped + (p,))) for p in paths]
    # Get tree for base:
    tree_base = repo.commit(ref_base).tree
    if ref_remote is None:
        # Diff tree against working copy:
        diff = tree_base.diff(None, paths)
    else:
        # Get remote tree and diff against base:
        tree_remote = repo.commit(ref_remote).tree
        diff = tree_base.diff(tree_remote, paths)
    for entry in diff:
        fa = _get_diff_entry_stream(
            entry.a_path, entry.a_blob, ref_base, repo_dir)
        if fa is None:
            continue
        fb = _get_diff_entry_stream(
            entry.b_path, entry.b_blob, ref_remote, repo_dir)
        if fb is None:
            continue
        yield (fa, fb)
