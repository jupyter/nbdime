# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os
import re
import requests

import pytest

import nbformat

from .utils import WEB_TEST_TIMEOUT, wait_up, TEST_TOKEN


_re_config = re.compile(
    """<script id='nbdime-config-data' type="application/json">(.*?)</script>"""
)


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_isgit(git_repo2, server_extension_app):
    url = 'http://127.0.0.1:%i/nbdime/api/isgit' % server_extension_app['port']
    r = requests.post(
        url,
        data=json.dumps({
            'path': git_repo2,
        }),
        headers={
            'Authorization': 'token %s' % TEST_TOKEN
        })
    r.raise_for_status()
    assert r.json() == {'is_git': True}


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_isgit_nonrepo(git_repo2, server_extension_app):
    url = 'http://127.0.0.1:%i/nbdime/api/isgit' % server_extension_app['port']
    r = requests.post(
        url,
        data=json.dumps({
            'path': server_extension_app['path'],
        }),
        headers={
            'Authorization': 'token %s' % TEST_TOKEN
        })
    r.raise_for_status()
    assert r.json() == {'is_git': False}


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_difftool(git_repo2, server_extension_app):
    url = 'http://127.0.0.1:%i/nbdime/difftool' % server_extension_app['port']
    r = requests.get(
        url,
        headers={
            'Authorization': 'token %s' % TEST_TOKEN
        })
    r.raise_for_status()


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_git_difftool(git_repo2, server_extension_app):
    url = 'http://127.0.0.1:%i/nbdime/git-difftool' % server_extension_app['port']
    r = requests.get(
        url,
        headers={
            'Authorization': 'token %s' % TEST_TOKEN
        })
    r.raise_for_status()
    assert r.text.startswith('<!DOCTYPE html')
    # Extract config data
    match = _re_config.search(r.text)
    data = json.loads(match.group(1))
    assert data == {
        "base": "git:",
        "baseUrl": "/nbdime",
        "closable": False,
        "remote": "",
        "savable": False
    }


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_diff_api(git_repo2, server_extension_app):
    local_path = os.path.relpath(git_repo2, server_extension_app['path'])
    url = 'http://127.0.0.1:%i/nbdime/api/diff' % server_extension_app['port']
    r = requests.post(
        url,
        data=json.dumps({
            'base': 'git:' + os.path.join(local_path, 'diff.ipynb'),
        }),
        headers={
            'Authorization': 'token %s' % TEST_TOKEN
        })
    r.raise_for_status()
    data = r.json()
    nbformat.validate(data['base'])
    assert data['diff']
    assert len(data.keys()) == 2


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_fails_without_token(git_repo2, server_extension_app):
    url = 'http://127.0.0.1:%i/nbdime/api/isgit' % server_extension_app['port']
    r = requests.post(
        url,
        data=json.dumps({
            'path': git_repo2,
        }))
    with pytest.raises(requests.HTTPError):
        r.raise_for_status()


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_fails_with_wrong_token(git_repo2, server_extension_app):
    url = 'http://127.0.0.1:%i/nbdime/api/isgit' % server_extension_app['port']
    r = requests.post(
        url,
        data=json.dumps({
            'path': git_repo2,
        }),
        headers={
            'Authorization': 'token wrong-token-here'
        })
    with pytest.raises(requests.HTTPError):
        r.raise_for_status()
