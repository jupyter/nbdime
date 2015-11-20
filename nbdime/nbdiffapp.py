"""Utilities for diffing notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import nbformat
import json
from jupyter_core.application import JupyterApp, base_flags
from ._version import __version__
from .diff.diff_notebooks import diff_notebooks

nbdiff_flags = {
}
nbdiff_flags.update(base_flags)

class NBDiffApp(JupyterApp):
    version = __version__

    description="""Compute the diff of two Jupyter notebooks.
    """

    examples = """
    jupyter nbdiff before.ipynb after.ipynb patch.json
    """

    flags = nbdiff_flags

    def start(self):
        if len(self.extra_args) != 3:
            self.log.critical("Specify filenames of exactly two notebooks to diff and the output patch json filename.")
            self.exit(1)
        afn, bfn, dfn = self.extra_args
        if not os.path.exists(afn):
            self.log.critical("Missing file {}".format(afn))
            self.exit(1)
        if not os.path.exists(bfn):
            self.log.critical("Missing file {}".format(bfn))
            self.exit(1)

        a = nbformat.read(afn, as_version=4)
        b = nbformat.read(bfn, as_version=4)

        d = diff_notebooks(a, b)

        verbose = True
        if verbose:
            print(d)

        with open(dfn, "w") as df:
            json.dump(d, df)

def main():
    NBDiffApp.launch_instance()
