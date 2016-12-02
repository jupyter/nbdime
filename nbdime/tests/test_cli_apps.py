# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import io
import json
import logging
import os
from subprocess import CalledProcessError, Popen, PIPE
import time

import pytest
from pytest import mark
import requests
from tornado.httputil import url_concat

import nbformat

from .fixtures import filespath, assert_clean_exit, get_output, call

import nbdime
from nbdime.nbshowapp import main_show
from nbdime.nbdiffapp import main_diff
from nbdime.nbmergeapp import main_merge
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


def test_nbshow_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")

    args = nbshowapp._build_arg_parser().parse_args([afn, '--log-level=CRITICAL'])
    assert 0 == main_show(args)
    assert args.log_level == 'CRITICAL'
    assert nbdime.log.logger.level == logging.CRITICAL


def test_nbpatch_app(capsys):
    # this entrypoint is not exported,
    # but exercise it anyway
    p = filespath()
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    dfn = os.path.join(p, "multilevel-test-base-local-diff.json")
    assert 0 == nbpatchapp.main([bfn, dfn])


def test_nbdiff_app():
    p = filespath()
    afn = os.path.join(p, "multilevel-test-base.ipynb")
    bfn = os.path.join(p, "multilevel-test-local.ipynb")

    # When filename is omitted, will print to console instead
    #dfn = ""  # os.path.join(p, "multilevel-test-local-diff.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--log-level=WARN'])
    assert 0 == main_diff(args)
    assert args.log_level == 'WARN'
    assert nbdime.log.logger.level == logging.WARN


def test_nbmerge_app(tempfiles, capsys):
    p = tempfiles
    bfn = os.path.join(p, "multilevel-test-base.ipynb")
    lfn = os.path.join(p, "multilevel-test-local.ipynb")
    rfn = os.path.join(p, "multilevel-test-remote.ipynb")
    ofn = os.path.join(p, "output.ipynb")

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


def test_nbmerge_app_conflict(tempfiles, capsys):
    p = tempfiles
    bfn = os.path.join(p, "inline-conflict--1.ipynb")
    lfn = os.path.join(p, "inline-conflict--2.ipynb")
    rfn = os.path.join(p, "inline-conflict--3.ipynb")
    ofn = os.path.join(p, "inline-conflict-out.ipynb")

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
    p = tempfiles
    bfn = os.path.join(p, "inline-conflict--1.ipynb")
    lfn = os.path.join(p, "inline-conflict--2.ipynb")
    rfn = os.path.join(p, "inline-conflict--3.ipynb")
    ofn = os.path.join(p, "inline-conflict-out.ipynb")

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
    assert os.path.exists('.gitattributes')
    with io.open('.gitattributes', 'r', encoding='utf8') as f:
        gitattributes = f.read()
    assert 'jupyternotebook' in gitattributes
    out = get_output('git config --get --local diff.jupyternotebook.command')
    assert 'git-nbdiffdriver' in out

    main(['config', '--disable'])
    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local diff.jupyternotebook.command')


def test_difftool_config(git_repo):
    main = nbdime.gitdifftool.main

    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    out = get_output('git config --get --local difftool.nbdime.cmd')
    assert 'git-nbdifftool' in out

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local diff.guitool')

    main(['config', '--enable', '--set-default'])
    out = get_output('git config --get --local diff.guitool')
    assert 'nbdime' == out.strip()

    main(['config', '--disable'])
    
    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local diff.guitool')


def test_mergedriver_config(git_repo):
    main = nbdime.gitmergedriver.main
    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    assert os.path.exists('.gitattributes')
    with io.open('.gitattributes', 'r', encoding='utf8') as f:
        gitattributes = f.read()
    assert 'jupyternotebook' in gitattributes
    out = get_output('git config --get --local merge.jupyternotebook.driver')
    assert 'git-nbmergedriver' in out

    main(['config', '--disable'])
    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local merge.jupyternotebook.driver')


def test_mergetool_config(git_repo):
    main = nbdime.gitmergetool.main
    with assert_clean_exit():
        main(['config', '-h'])

    main(['config', '--enable'])
    out = get_output('git config --get --local mergetool.nbdime.cmd')
    assert 'git-nbmergetool' in out

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local merge.tool')

    main(['config', '--enable', '--set-default'])
    out = get_output('git config --get --local merge.tool')
    assert 'nbdime' == out.strip()

    main(['config', '--disable'])

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local merge.tool')


def test_diffdriver(git_repo):
    nbdime.gitdiffdriver.main(['config', '--enable'])
    out = get_output('git diff base diff.ipynb')
    assert 'nbdiff' in out


def test_mergedriver(git_repo):
    p = filespath()
    # enable diff/merge drivers
    nbdime.gitdiffdriver.main(['config', '--enable'])
    nbdime.gitmergedriver.main(['config', '--enable'])
    # run merge with no conflicts
    out = get_output('git merge remote-no-conflict', err=True)
    assert 'nbmergeapp' in out
    with open('merge-no-conflict.ipynb') as f:
        merged = f.read()

    with open(os.path.join(p, 'multilevel-test-merged.ipynb')) as f:
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

    p = Popen(['git', 'difftool', '--tool=nbdime', 'base'])
    def _term():
        try:
            p.terminate()
        except OSError:
            pass
    request.addfinalizer(_term)
    
    # 3 is the number of notebooks in this diff
    url = 'http://127.0.0.1:%i' % port
    for i in range(3):
        while True:
            try:
                r = requests.get(url + '/difftool')
            except Exception as e:
                assert p.poll() is None
                print("waiting for nbdiff server %i" % i)
                time.sleep(0.2)
            else:
                break
        # server started
        r.raise_for_status()
        # close it
        r = requests.post(url + '/api/closetool', headers={'exit_code': '0'})
        r.raise_for_status()
        time.sleep(0.25)
    # wait for exit
    p.wait()
    assert p.poll() == 0


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
    p = Popen(['git', 'mergetool', '--no-prompt', '--tool=nbdime', 'merge-conflict.ipynb'])
    def _term():
        try:
            p.terminate()
        except OSError:
            pass
    request.addfinalizer(_term)
    
    # 3 is the number of notebooks in this diff
    url = 'http://127.0.0.1:%i' % port
    while True:
        try:
            r = requests.get(url + '/mergetool')
        except Exception as e:
            assert p.poll() is None
            print("waiting for nbmerge server")
            time.sleep(0.2)
        else:
            break
    # server started
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
    p.wait()
    assert p.poll() == 0

