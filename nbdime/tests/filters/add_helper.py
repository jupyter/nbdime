#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""
Test git filter for notebooks that adds a cell on clean, and removes it on smudge.

Useful, as it is both a deterministic, circular filter, but also one that
adds content on clean (normally it is the reverse).
"""

import argparse
import sys

import nbformat

from nbdime.utils import setup_std_streams


# Generate a marker
MARKER = 'nbdime test filter marker'


def _build_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'mode', default=None,
        help='The mode to run the filter in. Either "clean" or "smudge".')
    return parser


def clean(notebook):
    if get_marker_cell(notebook) is None:
        notebook['cells'].append(nbformat.v4.new_raw_cell(
            source=MARKER,
            id='filtered-cell',
        ))

def smudge(notebook):
    if get_marker_cell(notebook) is not None:
        notebook['cells'].pop()


def get_marker_cell(notebook):
    if not notebook['cells']:
        return None
    candidate = notebook['cells'][-1]
    if candidate['cell_type'] != 'raw':
        return None
    source = candidate['source']
    if source == MARKER:
        return candidate

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
