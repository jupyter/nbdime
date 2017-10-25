#!/usr/bin/env python
"""A mercurial external differ for notebooks.

Uses nbdime to create diffs for notebooks instead of plain text diffs of JSON.
See the documentation for how to correctly configure mercurial to use this.

Use with:

    hg extdiff -p hg-nbdiff [<commit> [<commit>]]
"""

from __future__ import print_function

import os
import sys

import nbdime
from nbdime.webapp import nbdifftool
from nbdime.diffing.directorydiff import diff_directories


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('hg-nbdiffweb', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    nbdifftool.build_arg_parser(parser)
    opts = parser.parse_args(args)
    nbdime.log.init_logging(level=opts.log_level)

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
