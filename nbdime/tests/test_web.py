# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import json

import pytest
from tornado import ioloop
from tornado.httputil import url_concat
from tornado.escape import json_encode, json_decode
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
@pytest.mark.gen_test
def test_fetch_diff(http_client, base_url, nbdime_base_url):
    url = url_concat(
        base_url + nbdime_base_url + '/diff',
        dict(base=diff_a, remote=diff_b))
    response = yield http_client.fetch(url)
    assert response.code == 200


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
@pytest.mark.gen_test
def test_api_diff(http_client, base_url, nbdime_base_url, diff_validator, filespath, auth_header):
    post_data = dict(base=diff_a, remote=diff_b)
    body = json_encode(post_data)

    url = base_url + nbdime_base_url + '/api/diff'
    response = yield http_client.fetch(url, method='POST', headers=auth_header, body=body)
    assert response.code == 200
    # Check that response is sane:
    data = json_decode(response.body)
    # Check that base is as expected:
    expected_base = nbformat.read(os.path.join(filespath, diff_a), as_version=4)
    assert json.dumps(data['base'], sort_keys=True) == json.dumps(expected_base, sort_keys=True)
    # Check that diff follows schema:
    diff_validator.validate(data['diff'])


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
@pytest.mark.gen_test
def test_fetch_merge(http_client, base_url, nbdime_base_url):
    url = url_concat(
        base_url + nbdime_base_url + '/merge',
        dict(base=merge_a, local=merge_b, remote=merge_c))
    response = yield http_client.fetch(url)
    assert response.code == 200


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
@pytest.mark.gen_test
def test_api_merge(http_client, base_url, nbdime_base_url, merge_validator, filespath, auth_header):
    post_data = dict(base=merge_a, local=merge_b, remote=merge_c)
    body = json_encode(post_data)

    url = base_url + nbdime_base_url + '/api/merge'
    response = yield http_client.fetch(url, method='POST', headers=auth_header, body=body)
    assert response.code == 200
    # Check that response is sane:
    data = json_decode(response.body)
    # Check that base is as expected:
    expected_base = nbformat.read(os.path.join(filespath, merge_a), as_version=4)
    assert json.dumps(data['base'], sort_keys=True) == json.dumps(expected_base, sort_keys=True)
    # Check that decisions follows schema:
    merge_validator.validate(data['merge_decisions'])
