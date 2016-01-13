#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import json
from six import string_types
from tornado import ioloop, web
import nbformat
import nbdime


# TODO: See <notebook>/notebook/services/contents/handlers.py for possibly useful utilities:
#@json_errors
#contents_manager
#ContentsHandler
#APIHandler


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

    def get_notebook_argument(self, argname):
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(self.request.body)
        arg = body[argname]

        # Currently assuming arg is a filename relative to
        # where the server was started from, later we may
        # want to accept urls or full notebooks as well.
        if not isinstance(arg, string_types):
            raise web.HTTPError(400, "Expecting a filename.")

        # Check that file exists
        path = os.path.join(self.params["cwd"], arg)
        if not os.path.exists(path):
            raise web.HTTPError(400, "File doesn't exist: %s" % truncate_filename(arg))

        # Let nbformat do the reading and validation
        try:
            nb = nbformat.read(path, as_version=4)
        except:
            raise web.HTTPError(400, "Invalid notebook: %s" % truncate_filename(arg))

        return nb


class MainHandler(NbdimeApiHandler):
    def get(self):
        self.render("index.html")

class MainDiffHandler(NbdimeApiHandler):
    def get(self):
        # Currently just using the same file for both diff and merge
        self.render("index.html")

class MainMergeHandler(NbdimeApiHandler):
    def get(self):
        # Currently just using the same file for both diff and merge
        self.render("index.html")


class ApiDiffHandler(NbdimeApiHandler):
    def post(self):
        base_nb = self.get_notebook_argument("base")
        remote_nb = self.get_notebook_argument("remote")

        try:
            thediff = nbdime.diff_notebooks(base_nb, remote_nb)
        except Exception as e:
            raise web.HTTPError(400, "Error while diffing documents.")

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

        try:
            merged, lco, rco = nbdime.merge_notebooks(base_nb, local_nb, remote_nb)
        except Exception as e:
            raise web.HTTPError(400, "Error while attempting to merge documents.")

        data = {
            "base": base_nb,
            "local_conflicts": lco,
            "remote_conflicts": rco,
            }
        self.finish(data)


class ApiMergeStoreHandler(NbdimeApiHandler):
    def post(self):
        # I don't think we want to accept arbitrary filenames
        # to write to from the http request, only allowing
        # this operation if the server was run with an output
        # filename as a commandline argument:
        fn = self.params["outputfilename"]
        if not fn:
            raise web.HTTPError(400, "Server does not accept storing merge result.")
        path = os.path.join(self.params["cwd"], fn)

        body = json.loads(self.request.body)
        merged_nb = body["merged"]

        with open(path, "w") as f:
            nbformat.write(merged_nb, f)

        self.finish()


def make_app(**params):
    handlers = [
        (r"/", MainHandler, params),
        (r"/diff", MainDiffHandler, params),
        (r"/merge", MainMergeHandler, params),
        (r"/api/diff", ApiDiffHandler, params),
        (r"/api/merge", ApiMergeHandler, params),
        (r"/static", web.StaticFileHandler, {"path": static_path}),
        ]

    settings = {
        "static_path": static_path,
        "template_path": template_path,
        }

    DEBUGGING = 1
    if DEBUGGING:
        settings.update({
            "debug": True,
            })

    return web.Application(handlers, **settings)


def main(**params):
    print("Using params:")
    print(params)
    port = params.pop("port")
    app = make_app(**params)
    app.listen(port)
    ioloop.IOLoop.current().start()


if __name__ == "__main__":
    # TODO: Get (some of) these from cli arguments
    cwd = os.path.abspath(os.path.curdir)
    main(port=8888, cwd=cwd, outputfilename="")

