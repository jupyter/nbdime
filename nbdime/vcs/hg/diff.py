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

from nbdime import nbdiffapp
from nbdime.diffing.directorydiff import diff_directories
from nbdime.args import (
    add_diff_args, add_filename_args, diff_exclusives, process_exclusive_ignorables,
    add_diff_cli_args,
)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('hg-nbdiff', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    add_diff_args(parser)
    add_diff_cli_args(parser)
    add_filename_args(parser, ('base', 'remote'))

    opts = parser.parse_args(args)

    # TODO: Filter base/remote: If directories, find all modified notebooks
    # If files that are not notebooks, ensure a decent error is printed.
    if not os.path.isfile(opts.base) or not os.path.isfile(opts.remote):
        base, remote = opts.base, opts.remote
        for a, b in diff_directories(base, remote):
            opts.base, opts.remote = a, b
            ret = nbdiffapp.main_diff(opts)
            if ret != 0:
                return ret
        return ret
    else:
        return nbdiffapp.main_diff(opts)



if __name__ == "__main__":
    sys.exit(main())
