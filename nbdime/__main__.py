# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import sys


def main_dispatch(args=None):
    if args is None:
        args = sys.argv[1:]
    cmd = args[0]
    args = args[1:]

    if cmd == "nbdiff":
        from nbdime.nbdiffapp import main
    elif cmd == "nbmerge":
        from nbdime.nbmergeapp import main
    elif cmd == "nbpatch":
        from nbdime.nbpatchapp import main
    elif cmd == "nbdiff-web":
        from nbdime.webapp.nbdiffweb import main
    elif cmd == "nbmerge-web":
        from nbdime.webapp.nbmergeweb import main
    else:
        print(
            "Invalid command '%s', expecting one of:\n"
            "  nbdiff, nbmerge, nbpatch, nbdiff-web, nbmerge-web." % (cmd,))
        return 1

    return main(args)


if __name__ == "__main__":
    # This is triggered by "python -m nbdime <args>"
    import nbdime.log
    nbdime.log.init_logging()
    sys.exit(main_dispatch())
