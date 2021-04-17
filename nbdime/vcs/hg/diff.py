#!/usr/bin/env python
"""A mercurial external differ for notebooks.

Uses nbdime to create diffs for notebooks instead of plain text diffs of JSON.
See the documentation for how to correctly configure mercurial to use this.

Use with:

    hg extdiff -p hg-nbdiff [<commit> [<commit>]]
"""



import os
import sys

from nbdime import nbdiffapp
from nbdime.args import (
    add_diff_args, add_filename_args, add_diff_cli_args, add_prettyprint_args,
    ConfigBackedParser,
)
from nbdime.diffing.directorydiff import diff_directories


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = ConfigBackedParser('hg-nbdiff', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    add_diff_args(parser)
    add_diff_cli_args(parser)
    add_prettyprint_args(parser)
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
