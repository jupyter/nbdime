# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import logging
import os
import shutil
import json
import glob
import io
import re
from subprocess import Popen
import sys

try:
    from unittest import mock
except ImportError:
    import mock

from jsonschema import Draft4Validator as Validator
from jsonschema import RefResolver
from pytest import fixture, skip
import nbformat

from .utils import call, have_git, have_hg, wait_up, TEST_TOKEN

from nbdime.diffing.notebooks import set_notebook_diff_targets

try:
    # Python >= 3.3
    from subprocess import TimeoutExpired
    def popen_wait(p, timeout):
        return p.wait(timeout)
except ImportError:
    import time
    class TimeoutExpired(Exception):
        pass
    def popen_wait(p, timeout):
        """backport of Popen.wait from Python 3"""
        for i in range(int(10 * timeout)):
            if p.poll() is not None:
                return
            time.sleep(0.1)
        if p.poll() is None:
            raise TimeoutExpired

pjoin = os.path.join

schema_dir = os.path.abspath(pjoin(os.path.dirname(__file__), ".."))


def testspath():
    return os.path.abspath(os.path.dirname(__file__))


@fixture(scope='session')
def filespath():
    return os.path.join(testspath(), "files")


@fixture
def tempfiles(tmpdir, filespath):
    """Fixture for copying test files into a temporary directory"""
    dest = tmpdir.join('testfiles')
    shutil.copytree(filespath, str(dest))
    return str(dest)


@fixture
def nocolor(request):
    """Disable color printing for test"""
    import nbdime.prettyprint as pp
    patch = mock.patch.multiple(
        pp,
        ADD=pp.ADD.replace(pp.GREEN, ''),
        REMOVE=pp.REMOVE.replace(pp.RED, ''),
        INFO=pp.INFO.replace(pp.BLUE, ''),
        RESET='',
        git_diff_print_cmd=pp.git_diff_print_cmd.replace(' --color-words', ''),
    )
    patch.start()
    request.addfinalizer(patch.stop)


@fixture(scope='session')
def needs_git():
    if not have_git:
        skip("requires git")


@fixture(scope='session')
def needs_hg():
    if not have_hg:
        skip("requires mercurial")


@fixture(scope='session')
def needs_symlink(tmpdir_factory):
    if not hasattr(os, 'symlink'):
        skip('requires symlink creation')
    tdir = tmpdir_factory.mktemp('check-symlinks')
    source = tdir.mkdir('source')
    try:
        with tdir.as_cwd():
            os.symlink(str(source), 'link')
    except OSError:
        skip('requires symlink creation')


@fixture
def git_repo(tmpdir, request, filespath, needs_git):
    repo = str(tmpdir.join('repo'))
    os.mkdir(repo)
    save_cwd = os.getcwd()
    os.chdir(repo)
    request.addfinalizer(lambda: os.chdir(save_cwd))
    call('git init'.split())

    # setup base branch
    src = filespath
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


@fixture
def git_repo2(tmpdir, request, filespath, needs_git):
    repo = str(tmpdir.join('repo'))
    os.mkdir(repo)
    save_cwd = os.getcwd()
    os.chdir(repo)
    request.addfinalizer(lambda: os.chdir(save_cwd))
    call('git init'.split())

    # setup base branch
    src = filespath
    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(repo, 'diff.ipynb'))
    os.mkdir('sub')
    shutil.copy(pjoin(src, 'foo--1.ipynb'), pjoin(repo, 'sub', 'subfile.ipynb'))
    call('git add --all')
    call('git commit -m "init base branch"')
    # create base alias for master
    call('git checkout -b base master')

    # setup local branch
    call('git checkout -b local master')
    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(repo, 'diff.ipynb'))
    shutil.copy(pjoin(src, 'foo--2.ipynb'), pjoin(repo, 'sub', 'subfile.ipynb'))
    call('git commit -am "create local branch"')

    # setup remote branch
    call('git checkout -b remote master')
    shutil.copy(pjoin(src, 'foo--2.ipynb'), pjoin(repo, 'sub', 'subfile.ipynb'))
    shutil.copy(pjoin(src, 'markdown-only--1.ipynb'), pjoin(repo, 'sub', 'added.ipynb'))
    call('git add --all')
    call('git commit -am "create remote branch"')

    # start on remote
    call('git checkout remote')
    call('git rm diff.ipynb')
    assert not os.path.exists('.gitattributes')
    return repo


@fixture
def hg_repo(tmpdir, request, filespath, needs_hg):
    repo = str(tmpdir.join('repo'))
    os.mkdir(repo)
    save_cwd = os.getcwd()
    os.chdir(repo)
    request.addfinalizer(lambda: os.chdir(save_cwd))
    call('hg init'.split())

    # setup base branch
    src = filespath
    call('hg bookmark base')
    shutil.copy(pjoin(src, 'multilevel-test-base.ipynb'), pjoin(repo, 'merge-no-conflict.ipynb'))
    shutil.copy(pjoin(src, 'inline-conflict--1.ipynb'), pjoin(repo, 'merge-conflict.ipynb'))
    shutil.copy(pjoin(src, 'src-and-output--1.ipynb'), pjoin(repo, 'diff.ipynb'))
    call('hg add')
    call('hg commit -m "init base brach"')

    # setup local branch
    call('hg bookmark local')
    shutil.copy(pjoin(src, 'multilevel-test-local.ipynb'), pjoin(repo, 'merge-no-conflict.ipynb'))
    shutil.copy(pjoin(src, 'inline-conflict--2.ipynb'), pjoin(repo, 'merge-conflict.ipynb'))
    shutil.copy(pjoin(src, 'src-and-output--2.ipynb'), pjoin(repo, 'diff.ipynb'))
    call('hg commit -m "create local branch"')

    # setup remote branch with conflict
    call('hg update base')
    call('hg bookmark remote-conflict')
    shutil.copy(pjoin(src, 'inline-conflict--3.ipynb'), pjoin(repo, 'merge-conflict.ipynb'))
    call('hg commit -m "create remote with conflict"')

    # setup remote branch with no conflict
    call('hg update base')
    call('hg bookmark remote-no-conflict')
    shutil.copy(pjoin(src, 'multilevel-test-remote.ipynb'), pjoin(repo, 'merge-no-conflict.ipynb'))
    call('hg commit -m "create remote with conflict"')

    # start on local
    call('hg update local')
    return repo


@fixture
def reset_log():
    # clear root logger handlers before test and reset afterwards
    handlers = list(logging.getLogger().handlers)
    logging.getLogger().handlers[:] = []
    yield
    logging.getLogger().handlers[:] = handlers


@fixture
def nbdime_base_url():
    return '/this%20is/the%08base_url'


@fixture
def app(nbdime_base_url, filespath):
    """This is a fixture used by the pytest-tornado plugin.

    It is indirectly called by all tests that use the `gen_test`
    test mark.
    """
    from nbdime.webapp.nbdimeserver import init_app
    return init_app(
        base_url=nbdime_base_url,
        port=0,
        cwd=filespath,
    )[0]


@fixture
def json_schema_diff(request):
    schema_path = os.path.join(schema_dir, 'diff_format.schema.json')
    with io.open(schema_path, encoding="utf8") as f:
        schema_json = json.load(f)
    return schema_json


@fixture
def diff_validator(request, json_schema_diff):
    return Validator(json_schema_diff)


@fixture
def json_schema_merge(request):
    schema_path = os.path.join(schema_dir, 'merge_format.schema.json')
    with io.open(schema_path, encoding="utf8") as f:
        schema_json = json.load(f)
    return schema_json


@fixture
def merge_validator(request, json_schema_merge):
    return Validator(
        json_schema_merge,
        resolver=RefResolver(
            'file://localhost/' + schema_dir.replace('\\', '/') + '/',
            json_schema_merge),
        # Ensure tuples validate to "array" schema type
        types={"array": (list, tuple)},
    )


class NBTestDataBase(object):
    def __init__(self):
        self.filespath = filespath()
        self.cache = {}
        filenames = glob.glob(os.path.join(self.filespath, "*.ipynb"))
        names = [os.path.basename(fn).replace(".ipynb", "") for fn in filenames]
        self.names = list(sorted(names))

        # Build groups on the form {basename: [list of names 'basename--subname']},
        r = re.compile("^(.*)--(.*)$")
        matches = [r.match(name) for name in self.names]
        basenames = set(m.groups()[0] for m in matches if m)
        self.groups = {basename: [name for name in self.names if name.startswith(basename)]
                       for basename in basenames}

    def __len__(self):
        return len(self.names)

    def __iter__(self):
        return self.keys()

    def __hasitem__(self, name):
        return name in self.names

    def keys(self):
        return iter(self.names)

    def values(self):
        return (self[name] for name in self.names)

    def items(self):
        return ((name, self[name]) for name in self.names)

    def __getitem__(self, name):
        if isinstance(name, int):
            name = self.names[name]
        # Cache file reads
        nbs = self.cache.get(name)
        if nbs is None:
            fn = os.path.join(self.filespath, name + ".ipynb")
            with io.open(fn, encoding="utf8") as f:
                nbs = f.read()
            self.cache[name] = nbs
        # But return a new notebook copy every time
        return nbformat.reads(nbs, as_version=4)

_db = NBTestDataBase()


def _any_nb_name():
    return _db.names


def _any_nb_pair_names():
    pairs = []
    names = _db.names
    for i in range(len(names)):
        for j in range(i, len(names)):
            pairs.append((names[i], names[j]))
    return pairs


def _matching_nb_pair_names():
    pairs = []
    for basename, names in sorted(_db.groups.items()):
        for i in range(len(names)):
            for j in range(i, len(names)):
                pairs.append((names[i], names[j]))
    return pairs


def _matching_nb_triplet_names():
    triplets = []
    for basename, names in sorted(_db.groups.items()):
        if basename in _db.names:
            for i in range(len(names)):
                for j in range(i, len(names)):
                    triplets.append((basename, names[i], names[j]))
    return triplets


@fixture
def db():
    return _db


@fixture(params=_any_nb_name())
def any_nb(request):
    return _db[request.param]


@fixture(params=_any_nb_pair_names())
def any_nb_pair(request):
    a, b = request.param
    return _db[a], _db[b]


@fixture(params=_matching_nb_pair_names())
def matching_nb_pairs(request):
    a, b = request.param
    return _db[a], _db[b]


@fixture(params=_matching_nb_triplet_names())
def matching_nb_triplets(request):
    a, b, c = request.param
    print(a, b, c)
    return _db[a], _db[b], _db[c]


_port = 62019


@fixture()
def unique_port():
    global _port
    _port += 1
    return _port


@fixture()
def reset_diff_targets():
    try:
        yield
    finally:
        # Reset diff targets (global variable)
        set_notebook_diff_targets()

@fixture()
def popen_with_terminator(request):

    def run_process(*args, **kwargs):
        process = Popen(*args, **kwargs)
        def _term():
            try:
                process.terminate()
            except OSError:
                pass
        request.addfinalizer(_term)
        return process

    return run_process



def create_server_extension_config(tmpdir_factory):
    path = tmpdir_factory.mktemp('server-extension-config')
    config = {
        "NotebookApp": {
            "nbserver_extensions": {
                "nbdime": True
            }
        }
    }
    config_str = json.dumps(config)
    if isinstance(config_str, bytes):
        config_str = unicode(config_str)
    path.join('jupyter_notebook_config.json').write_text(config_str, 'utf-8')
    return str(path)



@fixture(scope='module')
def server_extension_app(tmpdir_factory, request):

    def _kill_nb_app():
        try:
            process.terminate()
        except OSError:
            # already dead
            pass
        popen_wait(process, 10)

    config_dir = create_server_extension_config(tmpdir_factory)
    env = os.environ.copy()
    env.update({'JUPYTER_CONFIG_DIR': config_dir})

    port = unique_port()
    root_dir = str(tmpdir_factory.getbasetemp())

    os.chdir(root_dir)
    process = Popen([
        sys.executable, '-m', 'notebook',
         '--port=%i' % port,
        '--ip=127.0.0.1',
        '--no-browser', '--NotebookApp.token=%s' % TEST_TOKEN],
        env=env)

    request.addfinalizer(_kill_nb_app)

    url = 'http://127.0.0.1:%i' % port
    wait_up(url, check=lambda: process.poll() is None)

    return dict(process=process, port=port, path=root_dir)
