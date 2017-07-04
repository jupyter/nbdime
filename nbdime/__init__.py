# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from ._version import __version__

from .diffing import diff, diff_notebooks
from .patching import patch, patch_notebook
from .merging import merge_notebooks, decide_merge, apply_decisions


def load_jupyter_server_extension(nb_server_app):
    # Wrap this here to avoid pulling in webapp in a normal run
    from .webapp.nb_server_extension import _load_jupyter_server_extension
    _load_jupyter_server_extension(nb_server_app)


def _jupyter_server_extension_paths():
    return [{
        "module": "nbdime"
    }]


def _jupyter_nbextension_paths():
    return [dict(
        section="notebook",
        # the path is relative to the `nbdime` directory
        src="notebook_ext",
        # directory in the `nbextension/` namespace
        dest="nbdime",
        # _also_ in the `nbextension/` namespace
        require="nbdime/index")]


__all__ = [
    "__version__",
    "diff", "diff_notebooks",
    "patch", "patch_notebook",
    "decide_merge", "merge_notebooks", "apply_decisions",
    "load_jupyter_server_extension",
    ]
