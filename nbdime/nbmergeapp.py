"""Utilities for mergeing notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import nbformat
import json
from jupyter_core.application import JupyterApp, base_flags
from ._version import __version__
from .merge import merge_notebooks

nbmerge_flags = {
}
nbmerge_flags.update(base_flags)

class NBMergeApp(JupyterApp):
    version = __version__

    description="""Merge Jupyter notebooks.
    """

    examples = """
    jupyter nbmerge base.ipynb local.ipynb remote.ipynb merged.ipynb
    """

    flags = nbmerge_flags

    def start(self):
        if len(self.extra_args) != 4:
            self.log.critical("Specify filenames for four notebooks: base local remote merged.")
            self.exit(1)

        bfn, lfn, rfn, mfn = self.extra_args

        for fn in (bfn, lfn, rfn):
            if not os.path.exists(fn):
                self.log.critical("Missing file {}".format(fn))
                self.exit(1)

        b = nbformat.read(bfn, asversion=4)
        l = nbformat.read(lfn, asversion=4)
        r = nbformat.read(rfn, asversion=4)

        m = merge_notebooks(b, l, r)

        verbose = True
        if verbose:
            print(m)

        nbformat.write(mfn, m)

def main():
    NBMergeApp.launch_instance()
