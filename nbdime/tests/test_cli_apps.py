
from __future__ import unicode_literals

import pytest
import os

from .fixtures import filespath

from nbdime.nbdiffapp import main_diff
from nbdime.nbpatchapp import main_patch
from nbdime.nbmergeapp import main_merge


def test_nbdiff_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")
    bfn = os.path.join(p, "multilevel-test-local.ipynb")
    # When filename is omitted, will print to console instead
    dfn = ""  # os.path.join(p, "multilevel-test-local-diff.json")
    assert 0 == main_diff(afn, bfn, dfn)


def test_nbpatch_app():
    p = filespath()
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    dfn = os.path.join(p, "multilevel-test-base-local-diff.json")
    # When filename is omitted, will print to console instead
    afn = ""  # os.path.join(p, "multilevel-test-base-local.ipynb")
    assert 0 == main_patch(bfn, dfn, afn)


def test_nbmerge_app():
    p = filespath()
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    lfn = os.path.join(p, "multilevel-test-local.ipynb")
    rfn = os.path.join(p, "multilevel-test-remote.ipynb")
    # When filename is omitted, will print to console instead
    mfn = ""  # os.path.join(temppath, "multilevel-test-merged.ipynb")
    assert 0 == main_merge(bfn, lfn, rfn, mfn)
