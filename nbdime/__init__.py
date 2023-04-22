# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from functools import partial
from ._version import __version__

from .diffing import diff, diff_notebooks
from .patching import patch, patch_notebook
from .merging import merge_notebooks, decide_merge, apply_decisions


def _load_jupyter_server_extension(nb_server_app, nb6_entrypoint=False):
    # Wrap this here to avoid pulling in webapp in a normal run
    from .webapp.nb_server_extension import _load_jupyter_server_extension
    _load_jupyter_server_extension(nb_server_app, nb6_entrypoint=nb6_entrypoint)


load_jupyter_server_extension = partial(_load_jupyter_server_extension, nb6_entrypoint=True)


def _jupyter_server_extension_paths():
    return [{
        "module": "nbdime"
    }]


_jupyter_server_extension_points = _jupyter_server_extension_paths


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "nbdime-jupyterlab"
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
    "_load_jupyter_server_extension",
    "_jupyter_server_extension_points",
    "_jupyter_server_extension_paths",
    ]
