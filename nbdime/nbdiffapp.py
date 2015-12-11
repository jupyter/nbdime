"""Utilities for diffing notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import nbformat
import json
from jupyter_core.application import JupyterApp, base_flags
from ._version import __version__
from .diffing.notebooks import diff_notebooks
from .dformat import PATCH, INSERT, DELETE, REPLACE, SEQINSERT, SEQDELETE

nbdiff_flags = {
}
nbdiff_flags.update(base_flags)


# TODO: Improve and make a more reusable utility.
import pprint
def pretty_print_diff(d, indent=0):
    "Pretty-print a nbdime diff."
    indsep = " "*4
    ind = indsep*indent
    ind2 = indsep*(indent+1)

    pp = []
    for e in d:
        action = e[0]
        key = e[1]
        if action == DELETE:
            pp.append("{}{} {}".format(ind, action, key))
        elif action in (INSERT, REPLACE):
            lines = pprint.pformat(e[2]).splitlines()
            pp.append("{}{} {}".format(ind, action, key))
            pp.extend(ind2+line for line in lines)
        elif action == PATCH:
            lines = pretty_print_diff(e[2]).splitlines()
            pp.append("{}{} {}".format(ind, action, key))
            pp.extend(ind2+line for line in lines)
        elif action == SEQDELETE:
            pp.append("{}{} {}-{}".format(ind, action, key, e[2]))
        elif action == SEQINSERT:
            lines = pprint.pformat(e[2]).splitlines()
            pp.append("{}{} {}-{}".format(ind, action, key, len(e[2])))
            pp.extend(ind2+line for line in lines)
        else:
            error("Can't print {}".format(e[0]))
    return u"\n".join(pp)


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
            print(pretty_print_diff(d))

        with open(dfn, "w") as df:
            json.dump(d, df)
            # Verbose version:
            #json.dump(d, df, indent=4, separators=(",", ": "))

def main():
    NBDiffApp.launch_instance()
