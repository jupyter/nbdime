# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import os

from .fixtures import filespath

import nbdime
from nbdime.nbshowapp import main_show
from nbdime.nbdiffapp import main_diff
from nbdime.nbmergeapp import main_merge


def test_nbshow_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")

    args = nbdime.nbshowapp._build_arg_parser().parse_args([afn])
    assert 0 == main_show(args)


def test_nbdiff_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")
    bfn = os.path.join(p, "multilevel-test-local.ipynb")

    # When filename is omitted, will print to console instead
    #dfn = ""  # os.path.join(p, "multilevel-test-local-diff.json")

    args = nbdime.nbdiffapp._build_arg_parser().parse_args([afn, bfn])
    assert 0 == main_diff(args)


def test_nbmerge_app():
    p = filespath()
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    lfn = os.path.join(p, "multilevel-test-local.ipynb")
    rfn = os.path.join(p, "multilevel-test-remote.ipynb")

    # When filename is omitted, will print to console instead
    #mfn = ""  # os.path.join(temppath, "multilevel-test-merged.ipynb")

    args = nbdime.nbmergeapp._build_arg_parser().parse_args([bfn, lfn, rfn])
    assert 0 == main_merge(args)
