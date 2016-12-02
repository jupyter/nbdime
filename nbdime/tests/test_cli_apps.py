# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import io
import logging
import os

import pytest
from pytest import mark

from .fixtures import filespath, assert_clean_exit

import nbformat

import nbdime
from nbdime.nbshowapp import main_show
from nbdime.nbdiffapp import main_diff
from nbdime.nbmergeapp import main_merge
from nbdime import (
    nbshowapp,
    nbdiffapp,
    nbmergeapp,
    gitdiffdriver,
    gitdifftool,
    gitmergedriver,
    gitmergetool,
)


def test_nbshow_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")

    args = nbdime.nbshowapp._build_arg_parser().parse_args([afn, '--log-level=CRITICAL'])
    assert 0 == main_show(args)
    assert args.log_level == 'CRITICAL'
    assert nbdime.log.logger.level == logging.CRITICAL


def test_nbdiff_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")
    bfn = os.path.join(p, "multilevel-test-local.ipynb")

    # When filename is omitted, will print to console instead
    #dfn = ""  # os.path.join(p, "multilevel-test-local-diff.json")

    args = nbdime.nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--log-level=WARN'])
    assert 0 == main_diff(args)
    assert args.log_level == 'WARN'
    assert nbdime.log.logger.level == logging.WARN


def test_nbmerge_app(tempfiles, capsys):
    p = tempfiles
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    lfn = os.path.join(p, "multilevel-test-local.ipynb")
    rfn = os.path.join(p, "multilevel-test-remote.ipynb")
    ofn = os.path.join(p, "output.ipynb")

    args = nbdime.nbmergeapp._build_arg_parser().parse_args([bfn, lfn, rfn, '--log-level=DEBUG'])
    assert args.log_level == 'DEBUG'
    assert nbdime.log.logger.level == logging.DEBUG

    assert 0 == main_merge(args)

    nb_stdout, err = capsys.readouterr()

    assert 0 == nbdime.nbmergeapp.main([bfn, lfn, rfn, '-o', ofn])
    out, err = capsys.readouterr()
    # no stdout when sending output to file
    assert out == ''

    assert os.path.exists(ofn)

    with io.open(ofn, 'r', encoding='utf8') as f:
        nb_file = f.read()

    assert nb_stdout == nb_file


def test_nbmerge_app_conflict(tempfiles, capsys):
    p = tempfiles
    bfn = os.path.join(p, "inline-conflict--1.ipynb")
    lfn = os.path.join(p, "inline-conflict--2.ipynb")
    rfn = os.path.join(p, "inline-conflict--3.ipynb")
    ofn = os.path.join(p, "inline-conflict-out.ipynb")

    assert 1 == nbdime.nbmergeapp.main([bfn, lfn, rfn])
    nb_stdout, err = capsys.readouterr()

    assert 1 == nbmergeapp.main([bfn, lfn, rfn, '-o', ofn])
    out, err = capsys.readouterr()
    # no stdout when sending output to file
    assert out == ''

    assert os.path.exists(ofn)

    with io.open(ofn, 'r', encoding='utf8') as f:
        nb_file = f.read()

    assert nb_stdout == nb_file


def test_nbmerge_app_decisions(tempfiles, capsys, reset_log):
    p = tempfiles
    bfn = os.path.join(p, "inline-conflict--1.ipynb")
    lfn = os.path.join(p, "inline-conflict--2.ipynb")
    rfn = os.path.join(p, "inline-conflict--3.ipynb")
    ofn = os.path.join(p, "inline-conflict-out.ipynb")

    assert 1 == nbdime.nbmergeapp.main([bfn, lfn, rfn, '--decisions', '-o', ofn])
    out, err = capsys.readouterr()
    # decisions are logged to stderr:
    assert 'conflicted decisions' in err

    # Don't write output if decisions are requested
    assert out == ''
    assert not os.path.exists(ofn)


def test_diffdriver_config():
    with assert_clean_exit():
        nbdime.gitdiffdriver.main(['config', '-h'])


def test_difftool_config():
    with assert_clean_exit():
        nbdime.gitdifftool.main(['config', '-h'])


def test_mergedriver_config():
    with assert_clean_exit():
        nbdime.gitmergedriver.main(['config', '-h'])


def test_mergetool_config():
    with assert_clean_exit():
        nbdime.gitmergetool.main(['config', '-h'])
