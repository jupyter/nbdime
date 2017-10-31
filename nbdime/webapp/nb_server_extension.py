#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

import json

from notebook.utils import url_path_join
from tornado.web import HTTPError, escape
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

from ..gitfiles import changed_notebooks, is_path_in_repo, InvalidGitRepositoryError, BadName


class GitMainDifftoolHandler(NbdimeHandler):
    """Diff tool handler that also handles showing diff to git HEAD"""

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


class GitApiDiffHandler(ApiDiffHandler):
    """Diff API handler that also handles diff to git HEAD"""

    def post(self):
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        base = body['base']
        if not base.startswith('git:'):
            return super(GitApiDiffHandler, self).post()

        base = base[len('git:'):]
        try:
            for fbase, fremote in changed_notebooks('HEAD', None, base):
                base_nb = nbformat.read(fbase, as_version=4)
                remote_nb = nbformat.read(fremote, as_version=4)
                break  # there should only ever be one set of files
            else:
                # The filename was either invalid or unchanged
                # Assume unchanged, and let api handler deal with it if not
                base_nb = self.read_notebook(base)
                remote_nb = base_nb
        except (InvalidGitRepositoryError, BadName):
            raise HTTPError(422, 'Invalid notebook: %s' % base)

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


class IsGitHandler(NbdimeHandler, APIHandler):
    """API handler for querying if path is in git repo"""

    def post(self):
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        nb = body['path']

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
        (r'/nbdime/difftool', MainDifftoolHandler, params),
        (r'/nbdime/git-difftool', GitMainDifftoolHandler, params),
        (r'/nbdime/api/diff', GitApiDiffHandler, params),
        (r'/nbdime/api/isgit', IsGitHandler, params),
    ]

    # Prefix routes with base_url:
    base_url = web_app.settings.get('base_url', '/')
    handlers = [(url_path_join(base_url, h[0]), h[1], h[2]) for h in handlers]

    host_pattern = '.*$'
    web_app.add_handlers(host_pattern, handlers)
