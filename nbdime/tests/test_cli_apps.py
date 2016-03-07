
from __future__ import unicode_literals

import pytest
import os
from argparse import Namespace

from .fixtures import filespath

import nbdime
from nbdime.nbdiffapp import main_diff
from nbdime.nbpatchapp import main_patch
from nbdime.nbmergeapp import main_merge


def test_nbdiff_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")
    bfn = os.path.join(p, "multilevel-test-local.ipynb")

    # When filename is omitted, will print to console instead
    #dfn = ""  # os.path.join(p, "multilevel-test-local-diff.json")

    args = nbdime.nbdiffapp._build_arg_parser().parse_args([afn, bfn])
    assert 0 == main_diff(args)


def test_nbpatch_app():
    p = filespath()
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    dfn = os.path.join(p, "multilevel-test-base-local-diff.json")

    # When filename is omitted, will print to console instead
    #afn = ""  # os.path.join(p, "multilevel-test-base-local.ipynb")

    args = nbdime.nbpatchapp._build_arg_parser().parse_args([bfn, dfn])
    assert 0 == main_patch(args)


def test_nbmerge_app():
    p = filespath()
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    lfn = os.path.join(p, "multilevel-test-local.ipynb")
    rfn = os.path.join(p, "multilevel-test-remote.ipynb")

    # When filename is omitted, will print to console instead
    #mfn = ""  # os.path.join(temppath, "multilevel-test-merged.ipynb")

    args = nbdime.nbmergeapp._build_arg_parser().parse_args([bfn, lfn, rfn])
    assert 0 == main_merge(args)
