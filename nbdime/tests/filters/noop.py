#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""A no-op filter.
"""

import argparse
import sys

import nbformat

from nbdime.utils import setup_std_streams


def _build_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'mode', default=None,
        help='The mode to run the filter in. Either "clean" or "smudge".')
    return parser


def clean(notebook):
    pass


def smudge(notebook):
    pass


def do_filter(notebook, args):
    if args.mode == 'clean':
        return clean(notebook)
    elif args.mode == 'smudge':
        return smudge(notebook)

    raise argparse.ArgumentError(
        args.mode,
        'mode can only be "clean" or "smudge", got %r.' % args.mode
    )


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    setup_std_streams()
    nb = nbformat.read(sys.stdin, as_version=4)
    opts = _build_arg_parser().parse_args(args)
    do_filter(nb, opts)
    nbformat.write(nb, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
