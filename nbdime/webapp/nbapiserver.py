#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import sys

from jupyter_server.base.handlers import JupyterHandler, APIHandler
from jupyter_server.log import log_request
from tornado import web, escape

from .nbdimeserver import main_server

from ..args import ConfigBackedParser, add_server_args, args_for_server
from ..diffing.notebooks import diff_notebooks
from ..log import logger
from ..merging.notebooks import decide_notebook_merge
from ..nbmergeapp import _build_arg_parser as build_merge_parser


class NbApiHandler(JupyterHandler):
    def initialize(self, **params):
        self.params = params
        self.body = None

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs.get('exc_info', None)
        if exc_info:
            (etype, value, traceback) = exc_info
            if etype == web.HTTPError:
                self.set_header('Content-Type', 'text/plain')
                return self.finish(str(value))
        return super(NbApiHandler, self).write_error(status_code, **kwargs)

    def get_notebook_argument(self, argname):
        if not self.body:
            self.body = json.loads(escape.to_unicode(self.request.body))

        # Assuming a request of the form "{'argname':arg}"
        arg = self.body[argname]

        if not isinstance(arg, dict):
            raise web.HTTPError(400, 'Expecting a notebook JSON object.')

        try:
            # Convert dictionary to a v4 notebook object with nbformat
            from nbformat import versions, NBFormatError, reader, convert, validate
            (major, minor) = reader.get_version(arg)
            if major in versions:
                nb = versions[major].to_notebook_json(arg, minor=minor)
            else:
                raise NBFormatError('Unsupported nbformat version %s' % major)
            nb = convert(nb, 4)
        except Exception as e:
            self.log.exception(e)
            raise web.HTTPError(422, 'Invalid notebook: %s' % argname)

        return nb

class ApiDiffHandler(NbApiHandler, APIHandler):
    def post(self):
        base_nb = self.get_notebook_argument('base')
        remote_nb = self.get_notebook_argument('remote')

        try:
            thediff = diff_notebooks(base_nb, remote_nb)
        except Exception:
            logger.exception('Error diffing documents:')
            raise web.HTTPError(500, 'Error while attempting to diff documents')

        self.finish({
            'base': base_nb,
            'diff': thediff,
        })

class ApiMergeHandler(NbApiHandler, APIHandler):
    def post(self):
        base_nb = self.get_notebook_argument('base')
        local_nb = self.get_notebook_argument('local')
        remote_nb = self.get_notebook_argument('remote')
        merge_args = self.settings.get('merge_args')
        if merge_args is None:
            merge_args = build_merge_parser().parse_args(['', '', ''])
            merge_args.merge_strategy = 'mergetool'
            self.settings['merge_args'] = merge_args

        try:
            decisions = decide_notebook_merge(base_nb, local_nb, remote_nb,
                                              args=merge_args)
        except Exception:
            logger.exception('Error merging documents:')
            raise web.HTTPError(500, 'Error while attempting to merge documents')

        self.finish({
            'base': base_nb,
            'merge_decisions': decisions
        })

def make_app(**params):
    base_url = params.pop('base_url', '/')
    handlers = [
        (r'/api/diff', ApiDiffHandler, params),
        (r'/api/merge', ApiMergeHandler, params)
    ]
    if base_url != '/':
        prefix = base_url.rstrip('/')
        handlers = [
            (prefix + path, cls, params)
            for (path, cls, params) in handlers
        ]

    settings = {
        'log_function': log_request,
        'base_url': base_url,
        'local_hostnames': ['localhost', '127.0.0.1'],
    }

    app = web.Application(handlers, **settings)
    app.exit_code = 0
    return app

def _build_arg_parser():
    """
    Creates an argument parser that lets the user specify a port
    and displays a help message.
    """
    description = 'Hostable, secure api interface for Nbdime.'
    parser = ConfigBackedParser(description=description)
    add_server_args(parser)
    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = _build_arg_parser().parse_args(args)
    return main_server(make_app, **args_for_server(arguments))


if __name__ == '__main__':
    sys.exit(main())
