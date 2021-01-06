# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os
import re
import shutil

import pytest

import nbformat

from tornado.httpclient import HTTPError

from ..utils import pushd
from .utils import WEB_TEST_TIMEOUT, TEST_TOKEN, call


pjoin = os.path.join

_re_config = re.compile(
    """<script id='nbdime-config-data' type="application/json">(.*?)</script>"""
)

@pytest.fixture
def jp_server_config():
    return {
        "ServerApp": {
            "jpserver_extensions": {
                "nbdime": True
            }
        }
    }


def read_response(response):
    """Extract the useful pieces from a torando HTTPResponse object"""
    # raise exception if it exists.
    if response.error:
        raise response.error
    # Decode the body.
    body = response.body.decode()
    # Parse if it's JSON
    try:
        body = json.loads(body)
    # If the body is empty, set the body to None.
    except json.decoder.JSONDecodeError:
        pass
    code = response.code
    return code, body


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_isgit(git_repo2, jp_fetch):
    r = await jp_fetch(
        'nbdime/api/isgit',
        method='POST',
        body=json.dumps({
            'path': git_repo2,
        })
    )
    code, body = read_response(r)
    assert body == {'is_git': True}


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_isgit_nonrepo(git_repo2, jp_root_dir, jp_fetch):
    r = await jp_fetch(
        'nbdime/api/isgit',
        method='POST',
        body=json.dumps({
            # Give a random patch that doesn't have a git repo.
            'path': str(jp_root_dir),
        })
    )
    code, body = read_response(r)
    assert body == {'is_git': False}


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_difftool(git_repo2, jp_fetch):
    r = await jp_fetch('nbdime/difftool')
    code, body = read_response(r)
    assert code == 200


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_git_difftool(git_repo2, jp_fetch, jp_base_url):
    r = await jp_fetch(
        'nbdime/git-difftool',
    )
    code, body = read_response(r)
    assert body.startswith('<!DOCTYPE html')
    # Extract config data
    match = _re_config.search(body)
    data = json.loads(match.group(1))
    assert data == {
        "base": "git:",
        "baseUrl": jp_base_url + "nbdime",
        "closable": False,
        "remote": "",
        "savable": False,
        "hideUnchanged": True,
        "mathjaxConfig": "TeX-AMS-MML_HTMLorMML-full,Safe",
        "mathjaxUrl": "",
    }


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_diff_api(git_repo2, jp_fetch, jp_root_dir):
    local_path = os.path.relpath(git_repo2, jp_root_dir)
    r = await jp_fetch(
        'nbdime/api/diff',
        method="POST",
        body=json.dumps({
            'base': 'git:' + pjoin(local_path, 'diff.ipynb'),
        })
    )
    code, body = read_response(r)
    nbformat.validate(body['base'])
    assert body['diff']
    assert len(body.keys()) == 2


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT*6)
async def test_git_diff_api(git_repo2, filespath, jp_fetch, jp_root_dir):
    local_path = os.path.relpath(git_repo2, jp_root_dir)

    # Add a difference betweeen index and working tree:
    shutil.copy(
        pjoin(filespath, 'foo--1.ipynb'),
        pjoin(git_repo2, 'sub', 'subfile.ipynb')
    )

    def _make_ref(key):
        if key.lower() in ('working', 'index'):
            return {'special': key}
        return {'git': key}

    # Test various diffs:
    for args in (
        ('HEAD', 'WORKING', 'diff.ipynb'),
        ('HEAD', 'INDEX', 'diff.ipynb'),
        ('INDEX', 'HEAD', 'diff.ipynb'),
        ('INDEX', 'WORKING', 'sub/subfile.ipynb'),
        ('index', 'working', 'sub/subfile.ipynb'),
        ('iNdeX', 'WorKING', 'sub/subfile.ipynb'),
    ):
        print(args)
        r = await jp_fetch(
            'nbdime/api/gitdiff',
            method="POST",
            body=json.dumps({
                'ref_local': _make_ref(args[0]),
                'ref_remote': _make_ref(args[1]),
                'file_path': pjoin(local_path, args[2])
            })
        )
        code, body = read_response(r)
        nbformat.validate(body['base'])
        assert body['diff']
        assert len(body.keys()) == 2


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_diff_api_checkpoint(filespath, git_repo2, jp_fetch, jp_root_dir):
    local_path = os.path.relpath(jp_root_dir)

    # Create base
    src = filespath
    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(str(jp_root_dir), 'diff.ipynb'))

    url_path = pjoin(local_path, 'diff.ipynb')
    if os.sep == '\\':
        url_path = url_path.replace('\\', '/')

    print(url_path)

    r = await jp_fetch(
        'api/contents/%s/checkpoints' % url_path,
        method="POST",
        allow_nonstandard_methods=True
    )
    code, body = read_response(r)

    # Overwrite:
    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(str(jp_root_dir), 'diff.ipynb'))

    r = await jp_fetch(
        'nbdime/api/diff',
        method="POST",
        body=json.dumps({
            'base': 'checkpoint:' + url_path,
        })
    )
    code, body = read_response(r)
    nbformat.validate(body['base'])
    assert body['diff']
    assert len(body.keys()) == 2


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
async def test_diff_api_symlink(git_repo2, jp_fetch, jp_root_dir, needs_symlink):
    subdir = pjoin(jp_root_dir, 'has space', 'subdir')
    os.makedirs(subdir)
    symlink = pjoin(subdir, 'link')
    with pushd(subdir):
        call(['git', 'init'])
        with open('f', 'w') as f:
            f.write('stuff')
        call(['git', 'add', 'f'])
        call(['git', 'commit', '-m', 'initial commit'])
    os.symlink(git_repo2, symlink)

    local_path = os.path.relpath(symlink, jp_root_dir)

    r = await jp_fetch(
        'nbdime/api/diff',
        method='POST',
        body=json.dumps({
            'base': 'git:' + pjoin(local_path, 'diff.ipynb'),
        })
    )
    code, body = read_response(r)
    nbformat.validate(body['base'])
    assert body['diff']
    assert len(body.keys()) == 2


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
@pytest.mark.parametrize(
    # Set the auth header to nothing
    'jp_auth_header',
    ({},)
)
async def test_fails_without_token(git_repo2, jp_fetch, jp_auth_header):
    r = await jp_fetch(
        'nbdime/api/isgit',
        method='POST',
        body=json.dumps({
            'path': git_repo2,
        }),
        raise_error=False
    )
    # Assert that reading the response fails.
    with pytest.raises(HTTPError):
        code, body = read_response(r)
    # Assert that the code if 403, forbidden.
    assert r.code == 403


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
@pytest.mark.parametrize(
    # Set the auth header to bad header
    'jp_auth_header',
    ({'Authorization': 'token wrong-token-here'},)
)
async def test_fails_with_wrong_token(git_repo2, jp_fetch, jp_auth_header):
    r = await jp_fetch(
        'nbdime/api/isgit',
        method='POST',
        body=json.dumps({
            'path': git_repo2,
        }),
        raise_error=False
    )
    # Assert that reading the response fails.
    with pytest.raises(HTTPError):
        code, body = read_response(r)
    # Assert that the code if 403, forbidden.
    assert r.code == 403