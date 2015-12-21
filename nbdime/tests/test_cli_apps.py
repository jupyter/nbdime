
from __future__ import unicode_literals

import pytest

from nbdime.nbdiffapp import main_diff
from nbdime.nbpatchapp import main_patch
from nbdime.nbmergeapp import main_merge


@pytest.mark.xfail(reason="need to add actual test files")
def test_nbdiff_app():
    afn = "a.ipynb"
    bfn = "b.ipynb"
    dfn = "d.json"
    assert 0 == main_diff(afn, bfn, dfn)


@pytest.mark.xfail(reason="need to add actual test files")
def test_nbpatch_app():
    afn = "a.ipynb"
    dfn = "d.json"
    assert 0 == main_patch(afn, dfn)


@pytest.mark.xfail(reason="need to add actual test files")
def test_nbmerge_app():
    bfn = "b.ipynb"
    lfn = "l.ipynb"
    rfn = "r.ipynb"
    mfn = "m.ipynb"
    assert 0 == main_merge(bfn, lfn, rfn, mfn)
