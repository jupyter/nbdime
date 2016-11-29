# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import sys
from subprocess import call

try:
    from shutil import which
except ImportError:
    from backports.shutil_which import which

COMMANDS = ["show", "diff", "merge", "diff-web", "merge-web", "mergetool"]


def main_dispatch(args=None):
    if args is None:
        args = sys.argv[1:]
    if len(args) < 1:
        sys.exit("Command missing, expecting one of: \n%s" % ", ".join(COMMANDS))

    cmd = args[0]
    args = args[1:]

    if cmd == "show":
        from nbdime.nbshowapp import main
    elif cmd == "diff":
        from nbdime.nbdiffapp import main
    elif cmd == "merge":
        from nbdime.nbmergeapp import main
    elif cmd == "diff-web":
        from nbdime.webapp.nbdiffweb import main
    elif cmd == "merge-web":
        from nbdime.webapp.nbmergeweb import main
    elif cmd == 'mergetool':
        if not which('git'):
            sys.exit("Cannot use \"nbdime mergetool\" alias as git is not preset on path")
        to_call = 'git mergetool --tool=nbdimeweb *.ipynb'.split()
        return call(to_call)
    else:
        sys.exit(
            "Unrecognized command '%s', expecting one of:\n%s." %
            (cmd, ", ".join(COMMANDS)))

    return main(args)


if __name__ == "__main__":
    # This is triggered by "python -m nbdime <args>"
    sys.exit(main_dispatch())
