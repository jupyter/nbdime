#!/usr/bin/env python
"""A simple differ for diffing direcotries containing notebooks.

Does not handle file moves/renames, yet.
"""

import os
import filecmp
from nbdime.utils import EXPLICIT_MISSING_FILE

pjoin = os.path.join

# Lifted from http://stackoverflow.com/questions/4187564/recursive-dircmp-compare-two-directories-to-ensure-they-have-the-same-files-and
class dircmp(filecmp.dircmp):
    """
    Compare the content of dir1 and dir2. In contrast with filecmp.dircmp, this
    subclass compares the content of files with the same path.
    """

    def phase0(self):
        """
        Find the files on left and right for comparison.
        Ensure that we only consider notebook files or directories.
        """
        super(dircmp, self).phase0()
        self.left_list = filter(ipynb_only, self.left_list)
        self.right_list = filter(ipynb_only, self.right_list)

    def phase2(self):
        """
        Distinguish files, directories, funnies.
        Ensure files are only notebooks.
        """
        super(dircmp, self).phase2()
        self.common_files = filter(ipynb_only, self.common_files)

    def phase3(self):
        """
        Find out differences between common files.
        Ensure we are using content comparison with shallow=False.
        """
        fcomp = filecmp.cmpfiles(self.left, self.right, self.common_files,
                                 shallow=False)
        self.same_files, self.diff_files, self.funny_files = fcomp


def ipynb_only(path):
    return os.path.isdir(path) or os.path.splitext(path)[1] == '.ipynb'


def find_all_sub_notebooks(dirpath):
    for dirpath, _, filenames in os.walk(dirpath, topdown=False):
        for f in filenames:
            if os.path.splitext(f)[1] == '.ipynb':
                yield pjoin(dirpath, f)


def diff_directories(a, b, dc=None):
    """Iterate over differing files in two directories.

    Based on directory/file name only, so renames are handled as
    a full deletion + addition.
    """
    if dc is None:
        dc = dircmp(a, b, ignore=[])
    # Yield deleted files from current directory, or deleted directories:
    for deleted in dc.left_only:
        deleted = pjoin(dc.left, deleted)
        if os.path.isdir(deleted):
            for del_f in find_all_sub_notebooks(deleted):
                yield (del_f, EXPLICIT_MISSING_FILE)
        else:
            yield (deleted, EXPLICIT_MISSING_FILE)
    # Yield added files from current directory, or added directories:
    for added in dc.right_only:
        added = pjoin(dc.right, added)
        if os.path.isdir(added):
            for add_f in find_all_sub_notebooks(added):
                yield (EXPLICIT_MISSING_FILE, add_f)
        else:
            yield (EXPLICIT_MISSING_FILE, added)
    # Recurse for common directories:
    for _, sub_dc in dc.subdirs:
        yield from diff_directories(None, None, sub_dc)

    # Yield changed files from current directory:
    for changed in dc.diff_files:
        yield (pjoin(dc.left, changed), pjoin(dc.right, changed))
