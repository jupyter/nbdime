# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import json

import pytest
import requests
from tornado import ioloop
from tornado.httputil import url_concat
import nbformat

import nbdime.webapp.nbdiffweb
import nbdime.webapp.nbmergeweb

from .utils import WEB_TEST_TIMEOUT


diff_a = 'src-and-output--1.ipynb'
diff_b = 'src-and-output--2.ipynb'

merge_a = 'multilevel-test-base.ipynb'
merge_b = 'multilevel-test-local.ipynb'
merge_c = 'multilevel-test-remote.ipynb'



@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_diff_web(filespath, unique_port, reset_log, ioloop_patch):
    a = os.path.join(filespath, diff_a)
    b = os.path.join(filespath, diff_b)
    loop = ioloop.IOLoop.current()
    loop.call_later(0, loop.stop)
    nbdime.webapp.nbdiffweb.main(['--port=%i' % unique_port, '--browser=disabled', a, b])


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_diff_web_localhost(filespath, unique_port, reset_log, ioloop_patch):
    a = os.path.join(filespath, diff_a)
    b = os.path.join(filespath, diff_b)
    loop = ioloop.IOLoop.current()
    loop.call_later(0, loop.stop)
    nbdime.webapp.nbdiffweb.main([
        '--port=%i' % unique_port,
        '--browser=disabled',
        '--ip=localhost',
        a,
        b
    ])


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_diff_web_gitrefs(git_repo2, unique_port, reset_log, ioloop_patch):
    a = 'local'
    b = 'remote'
    c = 'diff.ipynb'
    d = 'sub/subfile.ipynb'
    loop = ioloop.IOLoop.current()
    loop.call_later(0, loop.stop)
    nbdime.webapp.nbdiffweb.main(['--port=%i' % unique_port, '--browser=disabled', a, b, c, d])


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_merge_web(filespath, unique_port, reset_log, ioloop_patch):
    a = os.path.join(filespath, merge_a)
    b = os.path.join(filespath, merge_b)
    c = os.path.join(filespath, merge_c)
    loop = ioloop.IOLoop.current()
    loop.call_later(0, loop.stop)
    nbdime.webapp.nbmergeweb.main(['--port=%i' % unique_port, '--browser=disabled', a, b, c])


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_fetch_diff(web_server, nbdime_base_url):
    url = url_concat(
        web_server + nbdime_base_url + '/diff',
        dict(base=diff_a, remote=diff_b))
    response = requests.get(url)
    assert response.status_code == 200


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_api_diff(web_server, nbdime_base_url, diff_validator, filespath, auth_header):
    post_data = dict(base=diff_a, remote=diff_b)

    url = web_server + nbdime_base_url + '/api/diff'
    response = requests.post(url, json=post_data, headers=auth_header)
    assert response.status_code == 200
    # Check that response is sane:
    data = response.json()
    # Check that base is as expected:
    expected_base = nbformat.read(os.path.join(filespath, diff_a), as_version=4)
    assert json.dumps(data['base'], sort_keys=True) == json.dumps(expected_base, sort_keys=True)
    # Check that diff follows schema:
    diff_validator.validate(data['diff'])


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_fetch_merge(web_server, nbdime_base_url):
    url = url_concat(
        web_server + nbdime_base_url + '/merge',
        dict(base=merge_a, local=merge_b, remote=merge_c))
    response = requests.get(url)
    assert response.status_code == 200


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_api_merge(web_server, nbdime_base_url, merge_validator, filespath, auth_header):
    post_data = dict(base=merge_a, local=merge_b, remote=merge_c)

    url = web_server + nbdime_base_url + '/api/merge'
    response = requests.post(url, json=post_data, headers=auth_header)
    assert response.status_code == 200
    # Check that response is sane:
    data = response.json()
    # Check that base is as expected:
    expected_base = nbformat.read(os.path.join(filespath, merge_a), as_version=4)
    assert json.dumps(data['base'], sort_keys=True) == json.dumps(expected_base, sort_keys=True)
    # Check that decisions follows schema:
    merge_validator.validate(data['merge_decisions'])
