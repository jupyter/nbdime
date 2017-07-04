#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function

from notebook.utils import url_path_join
from .nbdimeserver import (
    template_path,
    static_path,
    MainDifftoolHandler,
    ApiDiffHandler,
)


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
        (r'/nbdime/api/diff', ApiDiffHandler, params),
    ]

    # Prefix routes with base_url:
    base_url = web_app.settings.get('base_url', '/')
    handlers = [(url_path_join(base_url, h[0]), h[1], h[2]) for h in handlers]

    host_pattern = '.*$'
    web_app.add_handlers(host_pattern, handlers)
