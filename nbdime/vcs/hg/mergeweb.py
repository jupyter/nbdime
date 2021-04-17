#!/usr/bin/env python
"""A mercurial web-based merge tool for notebooks.

Uses nbdime to merge notebooks instead of plain text merges of JSON.
See the documentation for how to correctly configure mercurial to use this.

Use with:

    hg merge [<commit> [<commit>]]
"""



import argparse
import sys

from nbdime.args import ConfigBackedParser
from nbdime.webapp import nbmergetool


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = ConfigBackedParser('hg-nbmergeweb', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    nbmergetool.build_arg_parser(parser)

    opts = parser.parse_args(args)
    return nbmergetool.main_parsed(opts)


if __name__ == "__main__":
    sys.exit(main())
