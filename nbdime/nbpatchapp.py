"""Utilities for patching notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import nbformat
import json
from jupyter_core.application import JupyterApp, base_flags
from ._version import __version__
from .diff import patch_notebooks

nbpatch_flags = {
}
nbpatch_flags.update(base_flags)

class NBPatchApp(JupyterApp):
    version = __version__

    description="""Apply patch to a Jupyter notebook.
    """

    examples = """
    jupyter nbpatch before.ipynb patch.json -o after.ipynb
    """

    flags = nbdiff_flags

    def start(self):
        if len(self.extra_args) != 2:
            self.log.critical("Specify one notebook and one patch to apply.")
            self.exit(1)

        afn, dfn = self.extra_args

        for fn in (afn, dfn):
            if not os.path.exists(fn):
                self.log.critical("Missing file {}".format(fn))
                self.exit(1)

        a = nbformat.read(afn, asversion=4)
        d = json.load(dfn)

        b = patch_notebooks(a, d)

        verbose = True
        if verbose:
            print(b)

        nbformat.write(bfn, b)

def main():
    NBPatchApp.launch_instance()
