#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os

import io

from git import Repo, InvalidGitRepositoryError, BadName

from .utils import EXPLICIT_MISSING_FILE


# Ensure that we can use name attr:
class BlobWrapper(io.StringIO):
    name = ''


def get_repo(path):
    popped = []
    while True:
        try:
            repo = Repo()
            return (repo, popped)
        except InvalidGitRepositoryError:
            path, pop = os.path.split(path)
            if not pop:
                raise
            popped.append(pop)


def traverse_tree(tree, subdirs):
    if len(subdirs) == 0:
        return tree
    tree_map = {subtree.name: subtree for subtree in tree.trees}
    sub = subdirs[0]
    return traverse_tree(tree_map[sub], subdirs[1:])


def is_valid_gitref(ref, path=None):
    try:
        repo = get_repo(path)[0]
        repo.commit(ref)
        return True
    except InvalidGitRepositoryError:
        return False
    except BadName:
        return False


def changed_notebooks(ref_base, ref_remote, path=None):
    if path is None:
        # If path is not supplied, we diff entire repo
        repo = get_repo(os.curdir)[0]
        popped = []
    else:
        # If path is supplied, we only diff that part
        repo, popped = get_repo(path)
    # Get trees from refs:
    tree_base = traverse_tree(repo.commit(ref_base).tree, popped)
    tree_remote = traverse_tree(repo.commit(ref_remote).tree, popped)
    if ref_remote is None:
        # Diff tree against working copy:
        diff = tree_base.diff(None)
    else:
        diff = tree_base.diff(tree_remote)
    for entry in diff:
        if entry.a_path:
            if not entry.a_path.endswith('.ipynb'):
                continue
            if entry.a_blob is None:
                # Diffing against working copy, use file
                fa = io.open(entry.a_path)
            else:
                fa = BlobWrapper(entry.a_blob.data_stream.read().decode('utf-8'))
                fa.name = '%s (%s)' % (entry.a_path, ref_base)
        else:
            fa = EXPLICIT_MISSING_FILE
        if entry.b_path:
            if not entry.b_path.endswith('.ipynb'):
                continue
            if entry.b_blob is None:
                # Diffing against working copy, use file
                fb = io.open(entry.b_path)
            else:
                fb = BlobWrapper(entry.b_blob.data_stream.read().decode('utf-8'))
                fb.name = '%s (%s)' % (entry.b_path, ref_remote)
        else:
            fb = EXPLICIT_MISSING_FILE
        yield (fa, fb)
