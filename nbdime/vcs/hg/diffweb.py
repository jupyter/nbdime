#!/usr/bin/env python
"""A mercurial external differ for notebooks.

Uses nbdime to create diffs for notebooks instead of plain text diffs of JSON.
See the documentation for how to correctly configure mercurial to use this.

Use with:

    hg extdiff -p hg-nbdiff [<commit> [<commit>]]
"""



import os
import sys

from nbdime.args import ConfigBackedParser
from nbdime.webapp import nbdifftool
from nbdime.diffing.directorydiff import diff_directories


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = ConfigBackedParser('hg-nbdiffweb', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    nbdifftool.build_arg_parser(parser)
    opts = parser.parse_args(args)

    # TODO: If a/b are files that are not notebooks, ensure a decent error is printed.
    if not os.path.isfile(opts.local) or not os.path.isfile(opts.remote):
        local, remote = opts.local, opts.remote
        for a, b in diff_directories(local, remote):
            opts.local, opts.remote = a, b
            ret = nbdifftool.main_parsed(opts)
            if ret != 0:
                return ret
        return ret
    else:
        return nbdifftool.main_parsed(opts)



if __name__ == "__main__":
    sys.exit(main())
