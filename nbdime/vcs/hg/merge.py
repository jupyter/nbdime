#!/usr/bin/env python
"""A mercurial CLI merge tool for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.
See the documentation for how to correctly configure mercurial to use this.

Use with:

    hg merge [<commit> [<commit>]]
"""



import argparse
import sys

from nbdime import nbmergeapp
from nbdime.args import (
    add_generic_args, add_diff_args, add_merge_args, add_filename_args,
    ConfigBackedParser,
)



def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = ConfigBackedParser('hg-nbmerge', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    add_generic_args(parser)
    add_diff_args(parser)
    add_merge_args(parser)

    # Argument list, we are given base, local, remote
    add_filename_args(parser, ["base", "local", "remote", "merged"])

    opts = parser.parse_args(args)
    # mergeapp expects an additional decisions arg:
    opts.decisions = False
    opts.out = opts.merged
    del opts.merged
    return nbmergeapp.main_merge(opts)


if __name__ == "__main__":
    sys.exit(main())
