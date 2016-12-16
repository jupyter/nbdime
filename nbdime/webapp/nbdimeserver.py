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

import nbdime
from nbdime.merging.notebooks import decide_notebook_merge
from nbdime.nbmergeapp import _build_arg_parser as build_merge_parser

from nbdime.args import add_generic_args, add_web_args


# TODO: See <notebook>/notebook/services/contents/handlers.py for possibly useful utilities:
#@json_errors
#contents_manager
#ContentsHandler
#APIHandler


_logger = logging.getLogger(__name__)


here = os.path.abspath(os.path.dirname(__file__))
static_path = os.path.join(here, "static")
template_path = os.path.join(here, "templates")


def truncate_filename(name):
    limit = 20
    if len(name) < limit:
        return name
    else:
        return name[:limit-3] + "..."


class NbdimeApiHandler(web.RequestHandler):
    def initialize(self, **params):
        self.params = params
        self.base_url = params.get("base_url", "")

    def base_args(self):
        fn = self.params.get("outputfilename", None)
        return {
            "closable": self.params["closable"],
            "savable": fn is not None
        }

    def get_notebook_argument(self, argname):
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        arg = body[argname]

        # Currently assuming arg is a filename relative to
        # where the server was started from, later we may
        # want to accept urls or full notebooks as well.
        if not isinstance(arg, string_types):
            raise web.HTTPError(400, "Expecting a filename.")

        # Check that file exists
        path = os.path.join(self.params["cwd"], arg)
        if not os.path.exists(path):
            # Assume file is URI
            r = requests.get(arg)

        # Let nbformat do the reading and validation
        try:
            if os.path.exists(path):
                nb = nbformat.read(path, as_version=4)
            else:
                nb = nbformat.reads(r.text, as_version=4)
        except:
            raise web.HTTPError(400, "Invalid notebook: %s" % truncate_filename(arg))

        return nb


class MainHandler(NbdimeApiHandler):
    def get(self):
        args = self.base_args()
        args["base"] = self.get_argument("base", "")
        args["local"] = self.get_argument("local", "")
        args["remote"] = self.get_argument("remote", "")
        self.render("index.html", config_data=args, base_url=self.base_url)


class MainDiffHandler(NbdimeApiHandler):
    def get(self):
        args = self.base_args()
        args["base"] = self.get_argument("base", "")
        args["remote"] = self.get_argument("remote", "")

        self.render("diff.html", config_data=args, base_url=self.base_url)


class MainDifftoolHandler(NbdimeApiHandler):
    def get(self):
        args = self.base_args()
        if "difftool_args" in self.params:
            args["base"] = self.params["difftool_args"]["base"]
            args["remote"] = self.params["difftool_args"]["remote"]
        else:
            args["base"] = self.get_argument("base", "")
            args["remote"] = self.get_argument("remote", "")
        self.render("difftool.html", config_data=args, base_url=self.base_url)


class MainMergeHandler(NbdimeApiHandler):
    def get(self):
        args = self.base_args()
        args["base"] = self.get_argument("base", "")
        args["local"] = self.get_argument("local", "")
        args["remote"] = self.get_argument("remote", "")
        self.render("merge.html", config_data=args, base_url=self.base_url)


class MainMergetoolHandler(NbdimeApiHandler):
    def get(self):
        args = self.base_args()
        if "mergetool_args" in self.params:
            args["base"] = self.params["mergetool_args"]["base"]
            args["local"] = self.params["mergetool_args"]["local"]
            args["remote"] = self.params["mergetool_args"]["remote"]
        else:
            args["base"] = self.get_argument("base", "")
            args["local"] = self.get_argument("local", "")
            args["remote"] = self.get_argument("remote", "")
        self.render("mergetool.html", config_data=args, base_url=self.base_url)


class ApiDiffHandler(NbdimeApiHandler):
    def post(self):
        base_nb = self.get_notebook_argument("base")
        remote_nb = self.get_notebook_argument("remote")

        try:
            thediff = nbdime.diff_notebooks(base_nb, remote_nb)
        except Exception:
            nbdime.log.exception("Error diffing documents:")
            raise web.HTTPError(500, "Error while attempting to diff documents")

        data = {
            "base": base_nb,
            "diff": thediff,
            }
        self.finish(data)


class ApiMergeHandler(NbdimeApiHandler):
    def post(self):
        base_nb = self.get_notebook_argument("base")
        local_nb = self.get_notebook_argument("local")
        remote_nb = self.get_notebook_argument("remote")
        merge_args = self.settings.get('merge_args')
        if merge_args is None:
            merge_args = build_merge_parser().parse_args(["", "", ""])
            merge_args.merge_strategy = 'mergetool'
            self.settings['merge_args'] = merge_args

        try:
            decisions = decide_notebook_merge(base_nb, local_nb, remote_nb,
                                              args=merge_args)
        except Exception:
            nbdime.log.exception("Error merging documents:")
            raise web.HTTPError(500, "Error while attempting to merge documents")

        data = {
            "base": base_nb,
            "merge_decisions": decisions
            }
        self.finish(data)


class ApiMergeStoreHandler(NbdimeApiHandler):
    def post(self):
        # I don't think we want to accept arbitrary filenames
        # to write to from the http request, only allowing
        # this operation if the server was run with an output
        # filename as a commandline argument:
        fn = self.params.get("outputfilename", None)
        if not fn:
            raise web.HTTPError(400, "Server does not accept storing merge result.")
        path = os.path.join(self.params["cwd"], fn)
        nbdime.log.info("Saving merge result in %s", path)

        body = json.loads(escape.to_unicode(self.request.body))
        merged = body["merged"]
        merged_nb = nbformat.from_dict(merged)

        # Somehow store unsolved conflicts?
        # conflicts = body["conflicts"]

        with io.open(path, "w", encoding="utf8") as f:
            nbformat.write(merged_nb, f)
        self.finish()


class ApiCloseHandler(NbdimeApiHandler):
    def post(self):
        # Only allow closing, if started as tool
        if self.params.get('closable', False) is not True:
            raise web.HTTPError(
                400, "This server cannot be closed remotely.")

        # Fail if no exit code is supplied:
        self.application.exit_code = int(self.request.headers.get("exit_code", 1))

        _logger.info("Closing server on remote request")
        self.finish()
        ioloop.IOLoop.current().stop()


def make_app(**params):
    handlers = [
        (r"/", MainHandler, params),
        (r"/diff", MainDiffHandler, params),
        (r"/difftool", MainDifftoolHandler, params),
        (r"/merge", MainMergeHandler, params),
        (r"/mergetool", MainMergetoolHandler, params),
        (r"/api/diff", ApiDiffHandler, params),
        (r"/api/merge", ApiMergeHandler, params),
        (r"/api/store", ApiMergeStoreHandler, params),
        (r"/api/closetool", ApiCloseHandler, params),
        (r"/static", web.StaticFileHandler, {"path": static_path}),
    ]

    settings = {
        "static_path": static_path,
        "template_path": template_path,
        }

    if nbdime.utils.is_in_repo(nbdime.__file__):
        # don't cache when working from repo
        settings.update({
            # "autoreload": True,
            "compiled_template_cache": False,
            "static_hash_cache": False,
            # "serve_traceback": True,
            })

    app = web.Application(handlers, **settings)
    app.exit_code = 0
    return app


def main_server(on_port=None, closable=False, **params):
    _logger.debug("Using params: %s" % params)
    params.update({"closable": closable})
    port = params.pop("port")
    app = make_app(**params)
    if port != 0 or on_port is None:
        app.listen(port, address='127.0.0.1')
    else:
        sockets = netutil.bind_sockets(0, '127.0.0.1')
        server = httpserver.HTTPServer(app)
        server.add_sockets(sockets)
        for s in sockets:
            _logger.info('Listening on %s, port %d' % s.getsockname()[:2])
            port = s.getsockname()[1]
    if on_port is not None:
        on_port(port)
    ioloop.IOLoop.current().start()
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
    nbdime.log.init_logging(level=arguments.log_level)
    return main_server(port=arguments.port, cwd=arguments.workdirectory)


if __name__ == "__main__":
    sys.exit(main())
