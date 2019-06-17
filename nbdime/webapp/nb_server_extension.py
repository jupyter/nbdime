#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import json
import os

from jinja2 import ChoiceLoader, FileSystemLoader

from notebook.utils import url_path_join, to_os_path
from notebook.services.contents.checkpoints import GenericCheckpointsMixin
from notebook.services.contents.filecheckpoints import FileCheckpoints
from tornado.web import HTTPError, escape, authenticated, gen

from ..args import process_diff_flags
from ..config import build_config, Namespace
from ..diffing.notebooks import set_notebook_diff_ignores, diff_notebooks
from ..gitfiles import (
    changed_notebooks, is_path_in_repo, find_repo_root,
    InvalidGitRepositoryError, BadName, GitCommandNotFound,
    )
from ..ignorables import diff_ignorables
from ..utils import read_notebook

from .nbdimeserver import (
    template_path,
    static_path,
    NbdimeHandler,
    MainDifftoolHandler,
    ApiDiffHandler,
    APIHandler,
)


class AuthMainDifftoolHandler(MainDifftoolHandler):
    @authenticated
    def get(self):
        return super(AuthMainDifftoolHandler, self).get()


class GitDifftoolHandler(NbdimeHandler):
    """Diff tool handler that also handles showing diff to git HEAD"""

    @authenticated
    def get(self):
        args = self.base_args()
        args['base'] = 'git:' + self.get_argument('base', '')
        args['remote'] = ''

        self.write(self.render_template(
            'difftool.html',
            config_data=args,
            ))


class CheckpointDifftoolHandler(NbdimeHandler):
    """Diff tool handler that also handles showing diff to git HEAD"""

    @authenticated
    def get(self):
        args = self.base_args()
        args['base'] = 'checkpoint:' + self.get_argument('base', '')
        args['remote'] = ''

        self.write(self.render_template(
            'difftool.html',
            config_data=args,
            ))


class ExtensionApiDiffHandler(ApiDiffHandler):
    """Diff API handler that also handles diff to git HEAD"""

    @gen.coroutine
    def _get_checkpoint_notebooks(self, base):
        # Get the model for the current notebook:
        cm = self.contents_manager
        model = yield gen.maybe_future(cm.get(base, content=True, type='notebook'))
        remote_nb = model['content']
        # Get the model for the checkpoint notebook:
        checkpoints = yield gen.maybe_future(cm.list_checkpoints(base))
        if not checkpoints:
            # No checkpoints, indicate unchanged:
            self.log.info('No checkpoints for file: %r, %r', base, checkpoints)
            raise gen.Return((remote_nb, remote_nb))
        self.log.debug('Checkpoints: %r', checkpoints)
        checkpoint = checkpoints[0]
        if isinstance(cm.checkpoints, GenericCheckpointsMixin):
            checkpoint_model = yield gen.maybe_future(
                cm.checkpoints.get_notebook_checkpoint(checkpoint, base))
            base_nb = checkpoint_model['content']
        elif isinstance(cm.checkpoints, FileCheckpoints):
            path = yield gen.maybe_future(
                cm.checkpoints.checkpoint_path(checkpoint['id'], base))
            base_nb = read_notebook(path, on_null='minimal')
        else:
            raise RuntimeError('Unknown checkpoint handler interface')
        raise gen.Return((base_nb, remote_nb))

    @authenticated
    @gen.coroutine
    def post(self):
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        base = body['base']
        if base.startswith('git:'):
            base_nb, remote_nb = self.get_git_notebooks(base[len('git:'):])
        elif base.startswith('checkpoint:'):
            base_nb, remote_nb = yield self._get_checkpoint_notebooks(base[len('checkpoint:'):])
        else:
            # Regular files, call super
            super(ExtensionApiDiffHandler, self).post()
            return

        # Perform actual diff and return data:
        try:
            thediff = diff_notebooks(base_nb, remote_nb)
        except Exception:
            self.log.exception('Error diffing documents:')
            raise HTTPError(500, 'Error while attempting to diff documents')

        data = {
            'base': base_nb,
            'diff': thediff,
            }
        self.finish(data)

    @property
    def curdir(self):
        root_dir = getattr(self.contents_manager, 'root_dir', None)
        if root_dir is None:
            return super(ExtensionApiDiffHandler, self).curdir
        return root_dir


class GitDiffHandler(ApiDiffHandler):
    """Diff API handler that handles diffs for two git refs"""

    @authenticated
    @gen.coroutine
    def post(self):
        body = json.loads(escape.to_unicode(self.request.body))
        try:
            ref_prev = body['ref_prev']
            ref_curr = body['ref_curr']
            file_name = body['file_name']
        except KeyError:
            self.log.exception('Required keys ref_prev, ref_curr, file_name not provided in the request')
            raise HTTPError(400, 'Required keys ref_prev, ref_curr, file_name not provided in the request')

        base_nb, remote_nb = self.get_git_notebooks(file_name, ref_prev, ref_curr)

        # Perform actual diff and return data
        try:
            thediff = diff_notebooks(base_nb, remote_nb)
        except Exception:
            self.log.exception('Error diffing documents:')
            raise HTTPError(500, 'Error while attempting to diff documents')

        data = {
            'base': base_nb,
            'diff': thediff,
            }
        self.finish(data)

    @property
    def curdir(self):
        root_dir = getattr(self.contents_manager, 'root_dir', None)
        if root_dir is None:
            return super(ExtensionApiDiffHandler, self).curdir
        return root_dir

class IsGitHandler(NbdimeHandler, APIHandler):
    """API handler for querying if path is in git repo"""

    @authenticated
    def post(self):
        root_dir = getattr(self.contents_manager, 'root_dir', None)
        # Ensure notebooks are file-system based
        if root_dir is None:
            self.finish({'is_git': False})

        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        nb = os.path.join(root_dir, body['path'])

        data = {'is_git': is_path_in_repo(nb)}
        self.finish(data)


def _load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app

    env = web_app.settings['jinja2_env']

    env.loader = ChoiceLoader([
        env.loader,
        FileSystemLoader(template_path),
    ])

    config = build_config('extension')
    ignore = config.pop('Ignore', None)
    for k in diff_ignorables:
        config[k] = config.get(k, None)
    ns = Namespace(config)
    process_diff_flags(ns)
    if ignore:
        set_notebook_diff_ignores(ignore)

    web_app.settings['static_path'].append(static_path)

    params = {
        'nbdime_relative_base_url': 'nbdime',
        'closable': False,
    }
    handlers = [
        (r'/nbdime/difftool', AuthMainDifftoolHandler, params),
        (r'/nbdime/checkpoint-difftool', CheckpointDifftoolHandler, params),
        (r'/nbdime/git-difftool', GitDifftoolHandler, params),
        (r'/nbdime/api/diff', ExtensionApiDiffHandler, params),
        (r'/nbdime/api/isgit', IsGitHandler, params),
        (r'/nbdime/api/gitdiff', GitDiffHandler, params)
    ]

    # Prefix routes with base_url:
    base_url = web_app.settings.get('base_url', '/')
    handlers = [(url_path_join(base_url, h[0]), h[1], h[2]) for h in handlers]

    host_pattern = '.*$'
    web_app.add_handlers(host_pattern, handlers)
