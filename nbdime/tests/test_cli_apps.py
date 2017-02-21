# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import json
import logging
import os
from subprocess import CalledProcessError, Popen, check_call
import sys
import time

import pytest
import requests
from tornado.httputil import url_concat

import nbformat

from .utils import assert_clean_exit, get_output, call

import nbdime
from nbdime.nbshowapp import main_show
from nbdime.nbdiffapp import main_diff
from nbdime.nbmergeapp import main_merge
from nbdime.__main__ import main_dispatch
from nbdime import (
    nbshowapp,
    nbdiffapp,
    nbmergeapp,
    nbpatchapp,
    gitdiffdriver,
    gitdifftool,
    gitmergedriver,
    gitmergetool,
)
import nbdime.webapp.nbdiffweb
import nbdime.webapp.nbmergeweb
from nbdime.utils import EXPLICIT_MISSING_FILE


def test_nbshow_app(filespath):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")

    args = nbshowapp._build_arg_parser().parse_args([afn, '--log-level=CRITICAL'])
    assert 0 == main_show(args)
    assert args.log_level == 'CRITICAL'
    assert nbdime.log.logger.level == logging.CRITICAL


def test_nbpatch_app(capsys, filespath):
    # this entrypoint is not exported,
    # but exercise it anyway
    bfn = os.path.join(filespath, "multilevel-test-base.ipynb")
    dfn = os.path.join(filespath, "multilevel-test-base-local-diff.json")
    assert 0 == nbpatchapp.main([bfn, dfn])


def test_nbdiff_app(filespath):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    # When filename is omitted, will print to console instead
    # dfn = ""  # os.path.join(filespath, "multilevel-test-local-diff.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--log-level=WARN'])
    assert 0 == main_diff(args)
    assert args.log_level == 'WARN'
    assert nbdime.log.logger.level == logging.WARN


def test_nbdiff_app_null_file(filespath):
    fn = os.path.join(filespath, "multilevel-test-base.ipynb")

    args = nbdiffapp._build_arg_parser().parse_args([fn, EXPLICIT_MISSING_FILE])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args([EXPLICIT_MISSING_FILE, fn])
    assert 0 == main_diff(args)


def test_nbdiff_app_unicode_safe(filespath):
    afn = os.path.join(filespath, "unicode--1.ipynb")
    bfn = os.path.join(filespath, "unicode--2.ipynb")
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    env.pop('PYTHONIOENCODING', None)
    check_call([sys.executable, '-m', 'nbdime.nbdiffapp', afn, bfn], env=env)


def test_nbmerge_app(tempfiles, capsys):
    bfn = os.path.join(tempfiles, "multilevel-test-base.ipynb")
    lfn = os.path.join(tempfiles, "multilevel-test-local.ipynb")
    rfn = os.path.join(tempfiles, "multilevel-test-remote.ipynb")
    ofn = os.path.join(tempfiles, "output.ipynb")

    args = nbmergeapp._build_arg_parser().parse_args([bfn, lfn, rfn, '--log-level=DEBUG'])
    assert args.log_level == 'DEBUG'
    assert nbdime.log.logger.level == logging.DEBUG

    assert 0 == main_merge(args)

    nb_stdout, err = capsys.readouterr()

    assert 0 == nbmergeapp.main([bfn, lfn, rfn, '-o', ofn])
    out, err = capsys.readouterr()
    # no stdout when sending output to file
    assert out == ''

    assert os.path.exists(ofn)

    with io.open(ofn, 'r', encoding='utf8') as f:
        nb_file = f.read()

    assert nb_stdout == nb_file


def test_nbmerge_app_null_base(filespath):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    # Two identical files added (null base)
    args = nbmergeapp._build_arg_parser().parse_args([
        EXPLICIT_MISSING_FILE, afn, afn])
    assert 0 == main_merge(args)

    # Two conflicting files added (null base)
    args = nbmergeapp._build_arg_parser().parse_args([
        EXPLICIT_MISSING_FILE, afn, bfn])
    assert 1 == main_merge(args)


def test_nbmerge_app_null_side(filespath):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    # Local deleted, remote modified
    args = nbmergeapp._build_arg_parser().parse_args([
        afn, EXPLICIT_MISSING_FILE, bfn])
    assert 1 == main_merge(args)

    # Remote deleted, local modified
    args = nbmergeapp._build_arg_parser().parse_args([
        afn, bfn, EXPLICIT_MISSING_FILE])
    assert 1 == main_merge(args)

    # Both deleted
    args = nbmergeapp._build_arg_parser().parse_args([
        afn, EXPLICIT_MISSING_FILE, EXPLICIT_MISSING_FILE])
    assert 0 == main_merge(args)


def test_nbmerge_app_conflict(tempfiles, capsys):
    bfn = os.path.join(tempfiles, "inline-conflict--1.ipynb")
    lfn = os.path.join(tempfiles, "inline-conflict--2.ipynb")
    rfn = os.path.join(tempfiles, "inline-conflict--3.ipynb")
    ofn = os.path.join(tempfiles, "inline-conflict-out.ipynb")

    assert 1 == nbmergeapp.main([bfn, lfn, rfn])
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
    bfn = os.path.join(tempfiles, "inline-conflict--1.ipynb")
    lfn = os.path.join(tempfiles, "inline-conflict--2.ipynb")
    rfn = os.path.join(tempfiles, "inline-conflict--3.ipynb")
    ofn = os.path.join(tempfiles, "inline-conflict-out.ipynb")

    assert 1 == nbmergeapp.main([bfn, lfn, rfn, '--decisions', '-o', ofn])
    out, err = capsys.readouterr()
    # decisions are logged to stderr:
    assert 'conflicted decisions' in err

    # Don't write output if decisions are requested
    assert out == ''
    assert not os.path.exists(ofn)


def test_diffdriver_config(git_repo):
    main = nbdime.gitdiffdriver.main
    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    _check_diffdriver_enabled()

    main(['config', '--disable'])
    _check_diffdriver_disabled()


def _check_diffdriver_enabled():
    assert os.path.exists('.gitattributes')
    with io.open('.gitattributes', 'r', encoding='utf8') as f:
        gitattributes = f.read()
    assert 'jupyternotebook' in gitattributes
    out = get_output('git config --get --local diff.jupyternotebook.command')
    assert 'git-nbdiffdriver' in out


def _check_diffdriver_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local diff.jupyternotebook.command')


def test_difftool_config(git_repo):
    main = nbdime.gitdifftool.main

    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    _check_difftool_enabled()

    main(['config', '--enable', '--set-default'])
    out = get_output('git config --get --local diff.guitool')
    assert 'nbdime' == out.strip()

    main(['config', '--disable'])
    _check_difftool_disabled()


def _check_difftool_enabled():
    out = get_output('git config --get --local difftool.nbdime.cmd')
    assert 'git-nbdifftool' in out

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local diff.guitool')


def _check_difftool_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local diff.guitool')


def test_mergedriver_config(git_repo):
    main = nbdime.gitmergedriver.main
    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    _check_mergedriver_enabled()

    main(['config', '--disable'])
    _check_mergedriver_disabled()


def _check_mergedriver_enabled():
    assert os.path.exists('.gitattributes')
    with io.open('.gitattributes', 'r', encoding='utf8') as f:
        gitattributes = f.read()
    assert 'jupyternotebook' in gitattributes
    out = get_output('git config --get --local merge.jupyternotebook.driver')
    assert 'git-nbmergedriver' in out


def _check_mergedriver_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local merge.jupyternotebook.driver')


def test_mergetool_config(git_repo):
    main = nbdime.gitmergetool.main
    with assert_clean_exit():
        main(['config', '-h'])

    main(['config', '--enable'])
    _check_mergetool_enabled()

    main(['config', '--enable', '--set-default'])
    out = get_output('git config --get --local merge.tool')
    assert 'nbdime' == out.strip()

    main(['config', '--disable'])
    _check_mergetool_disabled()


def _check_mergetool_enabled():
    out = get_output('git config --get --local mergetool.nbdime.cmd')
    assert 'git-nbmergetool' in out

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local merge.tool')


def _check_mergetool_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local merge.tool')


def test_config_git(git_repo):
    """Check that `nbime config-git` command works"""

    main_dispatch(['config-git', '--enable'])

    _check_diffdriver_enabled()
    _check_difftool_enabled()
    _check_mergedriver_enabled()
    _check_mergetool_enabled()

    main_dispatch(['config-git', '--disable'])

    _check_diffdriver_disabled()
    _check_difftool_disabled()
    _check_mergedriver_disabled()
    _check_mergetool_disabled()


def test_config_git_fails(git_repo):
    """Check that `nbime config-git` command fails given invalid option"""
    # Check that it either gives non-zero return code (or exit code)
    try:
        code = main_dispatch(['config-git', '--foo'])
        assert code != 0
    except SystemExit as e:
        assert e.code != 0
    finally:
        _check_diffdriver_disabled()
        _check_difftool_disabled()
        _check_mergedriver_disabled()
        _check_mergetool_disabled()


def test_diffdriver(git_repo):
    nbdime.gitdiffdriver.main(['config', '--enable'])
    out = get_output('git diff base diff.ipynb')
    assert 'nbdiff' in out


def test_mergedriver(git_repo, filespath):
    # enable diff/merge drivers
    nbdime.gitdiffdriver.main(['config', '--enable'])
    nbdime.gitmergedriver.main(['config', '--enable'])
    # run merge with no conflicts
    out = get_output('git merge remote-no-conflict', err=True)
    assert 'nbmergeapp' in out
    with open('merge-no-conflict.ipynb') as f:
        merged = f.read()

    with open(os.path.join(filespath, 'multilevel-test-merged.ipynb')) as f:
        expected = f.read()

    # verify merge success
    assert merged == expected

    # reset
    call('git reset local --hard')

    # run merge with conflicts
    with pytest.raises(CalledProcessError):
        call('git merge remote-conflict')

    status = get_output('git status')
    assert 'merge-conflict.ipynb' in status
    out = get_output('git diff HEAD')
    assert 'nbdiff' in out
    # verify that the conflicted result is a valid notebook
    nb = nbformat.read('merge-conflict.ipynb', as_version=4)
    nbformat.validate(nb)


WEB_TEST_TIMEOUT = 15


def _wait_up(url, interval=0.1, check=None):
    while True:
        try:
            r = requests.get(url)
        except Exception as e:
            if check:
                assert check()
            print("waiting for %s" % url)
            time.sleep(interval)
        else:
            break


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_difftool(git_repo, request):
    nbdime.gitdifftool.main(['config', '--enable'])
    cmd = get_output('git config --get --local difftool.nbdime.cmd').strip()

    # pick a non-random port so we can connect later, and avoid opening a browser
    port = 62021
    cmd = cmd + ' --port=%i --browser=disabled' % port
    call(['git', 'config', 'difftool.nbdime.cmd', cmd])

    # avoid global diff driver config from disabling difftool:
    with open('.gitattributes', 'w') as f:
        f.write('*.ipynb\tdiff=notnbdime')

    process = Popen(['git', 'difftool', '--tool=nbdime', 'base'])

    def _term():
        try:
            process.terminate()
        except OSError:
            pass
    request.addfinalizer(_term)

    # 3 is the number of notebooks in this diff
    url = 'http://127.0.0.1:%i' % port
    for i in range(3):
        _wait_up(url, check=lambda: process.poll() is None)
        # server started
        r = requests.get(url + '/difftool')
        r.raise_for_status()
        # close it
        r = requests.post(url + '/api/closetool', headers={'exit_code': '0'})
        r.raise_for_status()
        time.sleep(0.25)
    # wait for exit
    process.wait()
    assert process.poll() == 0


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_mergetool(git_repo, request):
    nbdime.gitmergetool.main(['config', '--enable'])
    cmd = get_output('git config --get --local mergetool.nbdime.cmd').strip()

    # pick a non-random port so we can connect later, and avoid opening a browser
    port = 62022
    cmd = cmd + ' --port=%i --browser=disabled' % port
    call(['git', 'config', 'mergetool.nbdime.cmd', cmd])
    call(['git', 'config', 'mergetool.nbdime.trustExitCode', 'true'])

    with pytest.raises(CalledProcessError):
        call('git merge remote-conflict')
    process = Popen(['git', 'mergetool', '--no-prompt', '--tool=nbdime', 'merge-conflict.ipynb'])

    def _term():
        try:
            process.terminate()
        except OSError:
            pass
    request.addfinalizer(_term)

    # 3 is the number of notebooks in this diff
    url = 'http://127.0.0.1:%i' % port
    _wait_up(url, check=lambda: process.poll() is None)
    # server started
    r = requests.get(url + '/mergetool')
    r.raise_for_status()
    r = requests.post(
        url_concat(url + '/api/store', {'outputfilename': 'merge-conflict.ipynb'}),
        data=json.dumps({
            'merged': nbformat.v4.new_notebook(),
        })
    )
    r.raise_for_status()
    # close it
    r = requests.post(url + '/api/closetool', headers={'exit_code': '0'})
    r.raise_for_status()
    # wait for exit
    process.wait()
    assert process.poll() == 0
