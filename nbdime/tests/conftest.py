# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import logging
import os
import shutil
try:
    from unittest import mock
except ImportError:
    import mock

from pytest import yield_fixture, fixture, skip
import six

from .fixtures import filespath, call

try:
    from shutil import which
except ImportError:
    from backports.shutil_which import which

have_git = which('git')
pjoin = os.path.join


@fixture
def tempfiles(tmpdir):
    """Fixture for copying test files into a temporary directory"""
    dest = tmpdir.join('testfiles')
    shutil.copytree(filespath(), str(dest))
    return str(dest)


@fixture
def nocolor(request):
    """Disable color printing for test"""
    import nbdime.prettyprint as pp
    patch = mock.patch.multiple(pp,
        ADD=pp.ADD.replace(pp.GREEN,''),
        REMOVE=pp.REMOVE.replace(pp.RED,''),
        INFO=pp.INFO.replace(pp.BLUE,''),
        RESET='',
        git_diff_print_cmd=pp.git_diff_print_cmd.replace(' --color-words', ''),
    )
    patch.start()
    request.addfinalizer(patch.stop)

@fixture
def git_repo(tmpdir, request):
    if not have_git:
        skip("requires git")
    repo = str(tmpdir.join('repo'))
    os.mkdir(repo)
    save_cwd = os.getcwd()
    os.chdir(repo)
    request.addfinalizer(lambda : os.chdir(save_cwd))
    call('git init'.split())

    # setup base branch
    src = filespath()
    shutil.copy(pjoin(src, 'multilevel-test-base.ipynb'), pjoin(repo, 'merge-no-conflict.ipynb'))
    shutil.copy(pjoin(src, 'inline-conflict--1.ipynb'), pjoin(repo, 'merge-conflict.ipynb'))
    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(repo, 'diff.ipynb'))
    call('git add *.ipynb')
    call('git commit -m "init base branch"')
    # create base alias for master
    call('git checkout -b base master')

    # setup local branch
    call('git checkout -b local master')
    shutil.copy(pjoin(src, 'multilevel-test-local.ipynb'), pjoin(repo, 'merge-no-conflict.ipynb'))
    shutil.copy(pjoin(src, 'inline-conflict--2.ipynb'), pjoin(repo, 'merge-conflict.ipynb'))
    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(repo, 'diff.ipynb'))
    call('git commit -am "create local branch"')

    # setup remote branch with conflict
    call('git checkout -b remote-conflict master')
    shutil.copy(pjoin(src, 'inline-conflict--3.ipynb'), pjoin(repo, 'merge-conflict.ipynb'))
    call('git commit -am "create remote with conflict"')

    # setup remote branch with no conflict
    call('git checkout -b remote-no-conflict master')
    shutil.copy(pjoin(src, 'multilevel-test-remote.ipynb'), pjoin(repo, 'merge-no-conflict.ipynb'))
    call('git commit -am "create remote with no conflict"')

    # start on local
    call('git checkout local')
    assert not os.path.exists('.gitattributes')
    return repo


@yield_fixture
def reset_log():
    # clear root logger handlers before test and reset afterwards
    handlers = list(logging.getLogger().handlers)
    logging.getLogger().handlers[:] = []
    yield
    logging.getLogger().handlers[:] = handlers
