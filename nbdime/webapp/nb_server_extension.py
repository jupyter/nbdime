#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import json
import os

from notebook.utils import url_path_join, to_os_path
from notebook.services.contents.checkpoints import GenericCheckpointsMixin
from notebook.services.contents.filecheckpoints import FileCheckpoints
from tornado.web import HTTPError, escape, authenticated, gen
import nbformat

import nbdime
from .nbdimeserver import (
    template_path,
    static_path,
    NbdimeHandler,
    MainDifftoolHandler,
    ApiDiffHandler,
    APIHandler,
)

from ..gitfiles import (
    changed_notebooks, is_path_in_repo, find_repo_root,
    InvalidGitRepositoryError, BadName)
from ..utils import split_os_path, EXPLICIT_MISSING_FILE, read_notebook


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
            mathjax_url=self.mathjax_url,
            mathjax_config=self.mathjax_config,
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
            mathjax_url=self.mathjax_url,
            mathjax_config=self.mathjax_config,
            ))


class ExtensionApiDiffHandler(ApiDiffHandler):
    """Diff API handler that also handles diff to git HEAD"""

    def _get_git_notebooks(self, base_arg):
        # Sometimes the root dir of the files is not cwd
        nb_root = getattr(self.contents_manager, 'root_dir', None)
        # Resolve base argument to a file system path
        base = os.path.realpath(to_os_path(base_arg, nb_root))

        # Ensure path/root_dir that can be sent to git:
        try:
            git_root = find_repo_root(base)
        except InvalidGitRepositoryError as e:
            self.log.exception(e)
            raise HTTPError(422, 'Invalid notebook: %s' % base)
        base = os.path.relpath(base, git_root)

        # Get the base/remote notebooks:
        try:
            for fbase, fremote in changed_notebooks('HEAD', None, base, git_root):
                base_nb = read_notebook(fbase, on_null='minimal')
                remote_nb = read_notebook(fremote, on_null='minimal')
                break  # there should only ever be one set of files
            else:
                # The filename was either invalid or the file is unchanged
                # Assume unchanged, and let read_notebook handle error
                # reporting if invalid
                base_nb = self.read_notebook(os.path.join(git_root, base))
                remote_nb = base_nb
        except (InvalidGitRepositoryError, BadName) as e:
            self.log.exception(e)
            raise HTTPError(422, 'Invalid notebook: %s' % base_arg)
        return base_nb, remote_nb

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
            base_nb, remote_nb = self._get_git_notebooks(base[len('git:'):])
        elif base.startswith('checkpoint:'):
            base_nb, remote_nb = yield self._get_checkpoint_notebooks(base[len('checkpoint:'):])
        else:
            # Regular files, call super
            super(ExtensionApiDiffHandler, self).post()
            return

        # Perform actual diff and return data:
        try:
            thediff = nbdime.diff_notebooks(base_nb, remote_nb)
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
    env.loader.searchpath.append(template_path)
    web_app.settings['template_path'].append(template_path)

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
    ]

    # Prefix routes with base_url:
    base_url = web_app.settings.get('base_url', '/')
    handlers = [(url_path_join(base_url, h[0]), h[1], h[2]) for h in handlers]

    host_pattern = '.*$'
    web_app.add_handlers(host_pattern, handlers)
