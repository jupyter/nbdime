#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import io
import json
import logging
import os
import sys
from argparse import ArgumentParser

import requests
from six import string_types
from tornado import ioloop, web, escape, netutil, httpserver
import nbformat
from jinja2 import FileSystemLoader, Environment

import nbdime
from nbdime.merging.notebooks import decide_notebook_merge
from nbdime.nbmergeapp import _build_arg_parser as build_merge_parser
from nbdime.utils import EXPLICIT_MISSING_FILE

from nbdime.args import add_generic_args, add_web_args

from notebook.base.handlers import IPythonHandler, APIHandler
from notebook import DEFAULT_STATIC_FILES_PATH
from notebook.utils import url_path_join

# TODO: See <notebook>/notebook/services/contents/handlers.py for possibly useful utilities:
#@json_errors
#contents_manager
#ContentsHandler
#APIHandler


_logger = logging.getLogger(__name__)


here = os.path.abspath(os.path.dirname(__file__))
static_path = os.path.join(here, 'static')
template_path = os.path.join(here, 'templates')


class NbdimeHandler(IPythonHandler):
    def initialize(self, **params):
        self.params = params

    def base_args(self):
        fn = self.params.get('outputfilename', None)
        base = {
            'closable': self.params.get('closable', False),
            'savable': fn is not None,
            'baseUrl': self.nbdime_base_url,
        }
        if fn:
            # For reference, e.g. if user wants to download file
            base['outputfilename'] = fn
        return base

    def write_error(self, status_code, **kwargs):
        # Write error message for HTTPErrors if serve_traceback is off:
        exc_info = kwargs.get('exc_info', None)
        if exc_info and not self.settings.get('serve_traceback'):
            (etype, value, traceback) = exc_info
            if etype == web.HTTPError:
                self.set_header('Content-Type', 'text/plain')
                return self.finish(str(value))
        return super(IPythonHandler, self).write_error(status_code, **kwargs)

    def read_notebook(self, arg):
        # Currently assuming arg is a filename relative to
        # where the server was started from, later we may
        # want to accept urls or full notebooks as well.
        if not isinstance(arg, string_types):
            raise web.HTTPError(400, 'Expecting a filename or a URL.')

        try:
            # Check that file exists
            if arg == EXPLICIT_MISSING_FILE:
                path = arg
            else:
                path = os.path.join(self.curdir, arg)
                if not os.path.exists(path):
                    if '://' not in arg:
                        raise ValueError('Supplied argument cannot be read: %r' % arg)
                    # Assume file is URI
                    r = requests.get(arg)

            # Let nbformat do the reading and validation
            if os.path.exists(path):
                nb = nbformat.read(path, as_version=4)
            elif path == EXPLICIT_MISSING_FILE:
                nb = nbformat.v4.new_notebook()
            else:
                nb = nbformat.reads(r.text, as_version=4)
        except Exception as e:
            self.log.exception(e)
            raise web.HTTPError(422, 'Invalid notebook: %s' % arg)

        return nb

    def get_notebook_argument(self, argname):
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        arg = body[argname]

        return self.read_notebook(arg)

    @property
    def nbdime_base_url(self):
        relative = self.params.get('nbdime_relative_base_url', None)
        if relative is None:
            return self.base_url
        return url_path_join(self.base_url, relative)

    @property
    def curdir(self):
        return self.params.get('cwd', os.curdir)


class MainHandler(NbdimeHandler):
    def get(self):
        args = self.base_args()
        args['base'] = self.get_argument('base', '')
        args['local'] = self.get_argument('local', '')
        args['remote'] = self.get_argument('remote', '')
        self.write(self.render_template('compare.html',
                    config_data=args,
                    mathjax_url=self.mathjax_url,
                    mathjax_config=self.mathjax_config,
                   ))


class MainDiffHandler(NbdimeHandler):
    def get(self):
        args = self.base_args()
        args['base'] = self.get_argument('base', '')
        args['remote'] = self.get_argument('remote', '')

        self.write(self.render_template('diff.html',
                    config_data=args,
                    mathjax_url=self.mathjax_url,
                    mathjax_config=self.mathjax_config,
                   ))


class MainDifftoolHandler(NbdimeHandler):
    def get(self):
        args = self.base_args()
        if 'difftool_args' in self.params:
            base = self.params['difftool_args']['base']
            remote = self.params['difftool_args']['remote']
            if isinstance(base, string_types):
                args['base'] = base
            else:
                args['base'] = base.name
            if isinstance(remote, string_types):
                args['remote'] = remote
            else:
                args['remote'] = remote.name
        else:
            args['base'] = self.get_argument('base', '')
            args['remote'] = self.get_argument('remote', '')
        self.write(self.render_template('difftool.html',
                    config_data=args,
                    mathjax_url=self.mathjax_url,
                    mathjax_config=self.mathjax_config,
                   ))


class MainMergeHandler(NbdimeHandler):
    def get(self):
        args = self.base_args()
        args['base'] = self.get_argument('base', '')
        args['local'] = self.get_argument('local', '')
        args['remote'] = self.get_argument('remote', '')
        self.write(self.render_template('merge.html',
                    config_data=args,
                    mathjax_url=self.mathjax_url,
                    mathjax_config=self.mathjax_config,
                   ))


class MainMergetoolHandler(NbdimeHandler):
    def get(self):
        args = self.base_args()
        if 'mergetool_args' in self.params:
            args['base'] = self.params['mergetool_args']['base']
            args['local'] = self.params['mergetool_args']['local']
            args['remote'] = self.params['mergetool_args']['remote']
        else:
            args['base'] = self.get_argument('base', '')
            args['local'] = self.get_argument('local', '')
            args['remote'] = self.get_argument('remote', '')
        self.write(self.render_template('mergetool.html',
                    config_data=args,
                    mathjax_url=self.mathjax_url,
                    mathjax_config=self.mathjax_config,
                   ))


class ApiDiffHandler(NbdimeHandler, APIHandler):
    def post(self):
        base_nb = self.get_notebook_argument('base')
        remote_nb = self.get_notebook_argument('remote')

        try:
            thediff = nbdime.diff_notebooks(base_nb, remote_nb)
        except Exception:
            nbdime.log.exception('Error diffing documents:')
            raise web.HTTPError(500, 'Error while attempting to diff documents')

        data = {
            'base': base_nb,
            'diff': thediff,
            }
        self.finish(data)

    def get_notebook_argument(self, argname):
        if 'difftool_args' in self.params:
            arg = self.params['difftool_args'][argname]
            if not isinstance(arg, string_types):
                # Assume arg is file-like
                return nbformat.read(arg, as_version=4)
            return self.read_notebook(arg)
        return super(ApiDiffHandler, self).get_notebook_argument(argname)


class ApiMergeHandler(NbdimeHandler, APIHandler):
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
            nbdime.log.exception('Error merging documents:')
            raise web.HTTPError(500, 'Error while attempting to merge documents')

        data = {
            'base': base_nb,
            'merge_decisions': decisions
            }
        self.finish(data)

    def get_notebook_argument(self, argname):
        if 'mergetool_args' in self.params:
            arg = self.params['mergetool_args'][argname]
            return self.read_notebook(arg)
        return super(ApiMergeHandler, self).get_notebook_argument(argname)


class ApiMergeStoreHandler(NbdimeHandler, APIHandler):
    def post(self):
        # I don't think we want to accept arbitrary filenames
        # to write to from the http request, only allowing
        # this operation if the server was run with an output
        # filename as a commandline argument:
        fn = self.params.get('outputfilename', None)
        if not fn:
            raise web.HTTPError(400, 'Server does not accept storing merge result.')
        path = os.path.join(self.curdir, fn)
        nbdime.log.info('Saving merge result in %s', path)

        body = json.loads(escape.to_unicode(self.request.body))
        merged = body['merged']
        merged_nb = nbformat.from_dict(merged)

        # Somehow store unsolved conflicts?
        # conflicts = body['conflicts']

        with io.open(path, 'w', encoding='utf8') as f:
            nbformat.write(merged_nb, f)
        self.finish()


class ApiCloseHandler(NbdimeHandler, APIHandler):
    def post(self):
        # Only allow closing, if started as tool
        if self.params.get('closable', False) is not True:
            raise web.HTTPError(
                400, 'This server cannot be closed remotely.')

        # Fail if no exit code is supplied:
        self.application.exit_code = int(self.request.headers.get('exit_code', 1))

        _logger.info('Closing server on remote request')
        self.finish()
        ioloop.IOLoop.current().stop()


def make_app(**params):
    base_url = params.pop('base_url', '/')
    handlers = [
        (r'/', MainHandler, params),
        (r'/diff', MainDiffHandler, params),
        (r'/difftool', MainDifftoolHandler, params),
        (r'/merge', MainMergeHandler, params),
        (r'/mergetool', MainMergetoolHandler, params),
        (r'/api/diff', ApiDiffHandler, params),
        (r'/api/merge', ApiMergeHandler, params),
        (r'/api/store', ApiMergeStoreHandler, params),
        (r'/api/closetool', ApiCloseHandler, params),
        (r'/nb-static/mathjax/(.*)', web.StaticFileHandler, {
            'path': os.path.join(DEFAULT_STATIC_FILES_PATH, 'components', 'MathJax')
        })
        # Static handler will be added automatically
    ]
    if base_url != '/':
        prefix = base_url.rstrip('/')
        handlers = [
            (prefix + path, cls, params)
            for (path, cls, params) in handlers
        ]
    else:
        prefix = ''

    env = Environment(loader=FileSystemLoader([template_path]), autoescape=False)
    settings = {
        'static_path': static_path,
        'static_url_prefix': prefix + '/static/',
        'template_path': [template_path],
        'base_url': base_url,
        'jinja2_env': env,
        'mathjax_url': prefix + '/nb-static/mathjax/MathJax.js',
        }

    if nbdime.utils.is_in_repo(nbdime.__file__):
        # don't cache when working from repo
        settings.update({
            # 'autoreload': True,
            'compiled_template_cache': False,
            'static_hash_cache': False,
            # 'serve_traceback': True,
            })

    app = web.Application(handlers, **settings)
    app.exit_code = 0
    return app


def init_app(on_port=None, closable=False, **params):
    _logger.debug('Using params: %s' % params)
    params.update({'closable': closable})
    port = params.pop('port', 0)
    ip = params.pop('ip', '127.0.0.1')
    app = make_app(**params)
    if port != 0 or on_port is None:
        server = app.listen(port, address=ip)
        _logger.info('Listening on %s, port %d', ip, port)
    else:
        sockets = netutil.bind_sockets(0, ip)
        server = httpserver.HTTPServer(app)
        server.add_sockets(sockets)
        for s in sockets:
            _logger.info('Listening on %s, port %d', *s.getsockname()[:2])
            port = s.getsockname()[1]
    if on_port is not None:
        on_port(port)
    return app, server


def main_server(on_port=None, closable=False, **params):
    app, server = init_app(on_port, closable, **params)
    ioloop.IOLoop.current().start()
    # Clean up after server:
    server.stop()
    return app.exit_code


def _build_arg_parser():
    """
    Creates an argument parser that lets the user specify a port
    and displays a help message.
    """
    description = 'Web interface for Nbdime.'
    parser = ArgumentParser(description=description)
    add_generic_args(parser)
    add_web_args(parser)
    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    arguments = _build_arg_parser().parse_args(args)
    return main_server(port=arguments.port,
                       ip=arguments.ip,
                       cwd=arguments.workdirectory,
                       base_url=arguments.base_url,
                      )


if __name__ == '__main__':
    sys.exit(main())
