# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil

from nbdime.diffing.directorydiff import diff_directories
from nbdime.utils import EXPLICIT_MISSING_FILE

pjoin = os.path.join
relpath = os.path.relpath



def make_dirs(tmpdir):
    tmpdir.mkdir('dir1')
    tmpdir.mkdir('dir2')

    # Set up identical directory structures in both
    tmpdir.mkdir('dir1', 'subA')
    tmpdir.mkdir('dir2', 'subA')

    tmpdir.mkdir('dir1', 'subA', 'subsub')
    tmpdir.mkdir('dir2', 'subA', 'subsub')

    tmpdir.mkdir('dir1', 'subB')
    tmpdir.mkdir('dir2', 'subB')


def test_diff_root_files(tmpdir, filespath):
    src = filespath

    make_dirs(tmpdir)

    dir1 = str(tmpdir.join('dir1'))
    dir2 = str(tmpdir.join('dir2'))

    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(dir1, 'a.ipynb'))
    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(dir2, 'a.ipynb'))

    diffs = diff_directories(dir1, dir2)
    # Make paths relative for comparison:
    diffs = tuple((relpath(a, dir1), relpath(b, dir2)) for (a, b) in diffs)
    assert diffs == (('a.ipynb', 'a.ipynb'),)


def test_diff_sub_files(tmpdir, filespath):
    src = filespath

    make_dirs(tmpdir)

    dir1 = str(tmpdir.join('dir1'))
    dir2 = str(tmpdir.join('dir2'))

    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(dir1, 'subA', 'subsub', 'a.ipynb'))
    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(dir2, 'subA', 'subsub', 'a.ipynb'))

    diffs = diff_directories(dir1, dir2)
    # Make paths relative for comparison:
    diffs = tuple((relpath(a, dir1), relpath(b, dir2)) for (a, b) in diffs)
    assert diffs == ((pjoin('subA', 'subsub', 'a.ipynb'), pjoin('subA', 'subsub', 'a.ipynb')),)


def test_diff_file_added(tmpdir, filespath):
    src = filespath

    make_dirs(tmpdir)

    dir1 = str(tmpdir.join('dir1'))
    dir2 = str(tmpdir.join('dir2'))

    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(dir2, 'subA', 'subsub', 'a.ipynb'))

    diffs = diff_directories(dir1, dir2)
    # Make paths relative for comparison:
    diffs = tuple((a, relpath(b, dir2)) for (a, b) in diffs)
    assert diffs == ((EXPLICIT_MISSING_FILE, pjoin('subA', 'subsub', 'a.ipynb')),)


def test_diff_file_deleted(tmpdir, filespath):
    src = filespath

    make_dirs(tmpdir)

    dir1 = str(tmpdir.join('dir1'))
    dir2 = str(tmpdir.join('dir2'))

    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(dir1, 'subA', 'subsub', 'a.ipynb'))

    diffs = diff_directories(dir1, dir2)
    # Make paths relative for comparison:
    diffs = tuple((relpath(a, dir1), b) for (a, b) in diffs)
    assert diffs == ((pjoin('subA', 'subsub', 'a.ipynb'), EXPLICIT_MISSING_FILE),)

