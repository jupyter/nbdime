"""Utilities for patching notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import nbformat
import json
from jupyter_core.application import JupyterApp, base_flags
from ._version import __version__
from .diff.diff_notebooks import patch_notebook

nbpatch_flags = {
}
nbpatch_flags.update(base_flags)

class NBPatchApp(JupyterApp):
    version = __version__

    description="""Apply patch to a Jupyter notebook.
    """

    examples = """
    jupyter nbpatch before.ipynb patch.json after.ipynb
    """

    flags = nbpatch_flags

    def start(self):
        if len(self.extra_args) != 3:
            self.log.critical("Specify one notebook and one patch to apply.")
            self.exit(1)

        bfn, dfn, afn = self.extra_args

        for fn in (bfn, dfn):
            if not os.path.exists(fn):
                self.log.critical("Missing file {}".format(fn))
                self.exit(1)

        before = nbformat.read(bfn, as_version=4)
        with open(dfn) as df:
            d = json.load(df)

        after = patch_notebook(before, d)

        verbose = True
        if verbose:
            print(after)

        print "Writing", afn
        nbformat.write(after, afn)

def main():
    NBPatchApp.launch_instance()
