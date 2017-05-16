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
from nbdime.args import add_diff_args, add_filename_args, diff_exclusives, process_exclusive_ignorables


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser('hg-nbdiff', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    add_diff_args(parser)
    add_filename_args(parser, ('base', 'local'))

    opts = parser.parse_args(args)

    # TODO: Filter base/local: If directories, find all modified notebooks
    # If files that are not notebooks, ensure a decent error is printed.
    process_exclusive_ignorables(opts, diff_exclusives)
    filter_args = ['--%s' % name for name in diff_exclusives if getattr(opts, name)]
    if not os.path.isfile(opts.base) or not os.path.isfile(opts.local):
        for a, b in diff_directories(opts.base, opts.local):
            ret = nbdiffapp.main([a, b] + filter_args)
            if ret != 0:
                return ret
        return ret
    else:
        return nbdiffapp.main([opts.base, opts.local] + filter_args)



if __name__ == "__main__":
    sys.exit(main())
