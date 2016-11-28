# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import sys
COMMANDS = ["show", "diff", "merge", "patch", "diff-web", "merge-web"]


def main_dispatch(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) < 1:
        sys.exit("Please specify an nbdime command to call, such as 'nbdiff' or 'nbmerge'")

    cmd = args[0]
    args = args[1:]

    if cmd == "show":
        from nbdime.nbshowapp import main
    elif cmd == "diff":
        from nbdime.nbdiffapp import main
    elif cmd == "merge":
        from nbdime.nbmergeapp import main
    elif cmd == "patch":
        from nbdime.nbpatchapp import main
    elif cmd == "diff-web":
        from nbdime.webapp.nbdiffweb import main
    elif cmd == "merge-web":
        from nbdime.webapp.nbmergeweb import main
    else:
        sys.exit(
            "Unrecognized command '%s', expecting one of:\n%s." %
            (cmd, ", ".join(COMMANDS)))

    return main(args)


if __name__ == "__main__":
    # This is triggered by "python -m nbdime <args>"
    sys.exit(main_dispatch())
