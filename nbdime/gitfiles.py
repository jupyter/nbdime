#!/usr/bin/env python
# -*- coding:utf-8 -*-

import io
import os
from collections import deque

os.environ['GIT_PYTHON_REFRESH'] = 'quiet'
from git import (
    Repo, InvalidGitRepositoryError, BadName, NoSuchPathError,
    GitCommandNotFound, Diffable
)

from nbdime.vcs.git.filter_integration import apply_possible_filter
from .utils import EXPLICIT_MISSING_FILE, pushd


# Git ref representing the working tree
GitRefWorkingTree = None

# Git ref representing the index
GitRefIndex = Diffable.Index


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
    if path is missing, or the blob is None (unless diffing against working
    tree).
    """
    if path:
        if not path.endswith('.ipynb'):
            return None
        if ref_name is GitRefWorkingTree:
            # Diffing against working copy, use file on disk!
            with pushd(repo_dir):
                # We are diffing against working dir, so ensure we apply
                # any git filters before comparing:
                ret = apply_possible_filter(path)
                # ret == path means no filter was applied
                if ret != path:
                    return ret
                try:
                    return io.open(path, encoding='utf-8')
                except IOError:
                    return EXPLICIT_MISSING_FILE
        elif blob is None:
            # GitPython uses a None blob to indicate if a file was deleted or
            # added. Workaround for GitPython issue #749.
            return EXPLICIT_MISSING_FILE
        else:
            # There were strange issues with passing blob data_streams around,
            # so we solve this by reading into a StringIO buffer.
            # The penalty should be low as long as changed_notebooks are used
            # properly as an iterator.
            f = BlobWrapper(blob.data_stream.read().decode('utf-8'))
            f.name = '%s (%s)' % (
                path,
                ref_name if ref_name != GitRefIndex else '<INDEX>'
            )
            return f
    return EXPLICIT_MISSING_FILE


def changed_notebooks(ref_base, ref_remote, paths=None, repo_dir=None):
    """Iterator over all notebooks in path that has changed between the two git refs

    References are all valid values according to git-rev-parse, or one of
    the special sentinel values GitRefWorkingTree or GitRefIndex.

    Iterator value is a base/remote pair of streams to Notebooks
    or EXPLICIT_MISSING_FILE for added/removed files.
    """
    repo, popped = get_repo(repo_dir or os.curdir)
    if repo_dir is None:
        repo_dir = os.path.relpath(repo.working_tree_dir, os.curdir)
    if isinstance(paths, str):
        paths = (paths,)
    if paths and popped:
        # All paths need to be prepended by popped
        paths = [os.path.join(*(popped + (p,))) for p in paths]

    # Get tree/index for base
    if ref_base == GitRefIndex:
        tree_base = repo.index
    else:
        tree_base = repo.commit(ref_base).tree

    if ref_remote in (GitRefWorkingTree, GitRefIndex):
        diff = tree_base.diff(ref_remote, paths)
    else:
        # Get remote tree and diff against base:
        tree_remote = repo.commit(ref_remote).tree
        diff = tree_base.diff(tree_remote, paths)

    # Return the base/remote pair of Notebook file streams
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
