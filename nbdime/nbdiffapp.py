# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import argparse
import json

from six import string_types

from nbdime.diffing.notebooks import diff_notebooks
from nbdime.prettyprint import pretty_print_notebook_diff, PrettyPrintConfig
from nbdime.args import (
    add_generic_args, add_diff_args, process_diff_flags, resolve_diff_args,
    add_diff_cli_args,
    )
from nbdime.utils import EXPLICIT_MISSING_FILE, read_notebook, setup_std_streams
from .gitfiles import changed_notebooks, is_gitref


_description = "Compute the difference between two Jupyter notebooks."


def main_diff(args):
    """Main handler of diff CLI"""
    output = getattr(args, 'out', None)
    process_diff_flags(args)
    base, remote, paths = resolve_diff_args(args)

    # Check if base/remote are gitrefs:
    if is_gitref(base) and is_gitref(remote):
        # We are asked to do a diff of git revisions:
        status = 0
        for fbase, fremote in changed_notebooks(base, remote, paths):
            status = _handle_diff(fbase, fremote, output, args)
            if status != 0:
                # Short-circuit on error in diff handling
                return status
        return status
    else:  # Not gitrefs:
        return _handle_diff(base, remote, output, args)


def _handle_diff(base, remote, output, args):
    """Handles diffs of files, either as filenames or file-like objects"""
    # Check that if args are filenames they either exist, or are
    # explicitly marked as missing (added/removed):
    for fn in (base, remote):
        if (isinstance(fn, string_types) and not os.path.exists(fn) and
                fn != EXPLICIT_MISSING_FILE):
            print("Missing file {}".format(fn))
            return 1
    # Both files cannot be missing
    assert not (base == EXPLICIT_MISSING_FILE and remote == EXPLICIT_MISSING_FILE), (
        'cannot diff %r against %r' % (base, remote))

    # Perform actual work:
    a = read_notebook(base, on_null='empty')
    b = read_notebook(remote, on_null='empty')

    d = diff_notebooks(a, b)

    # Output as JSON to file, or print to stdout:
    if output:
        with open(output, "w") as df:
            # Compact version:
            #json.dump(d, df)
            # Verbose version:
            json.dump(d, df, indent=2, separators=(",", ": "))
    else:
        # This printer is to keep the unit tests passing,
        # some tests capture output with capsys which doesn't
        # pick up on sys.stdout.write()
        class Printer:
            def write(self, text):
                print(text, end="")
        # This sets up what to ignore:
        config = PrettyPrintConfig(out=Printer(), include=args, color_words=args.color_words)
        # Separate out filenames:
        base_name = base if isinstance(base, string_types) else base.name
        remote_name = remote if isinstance(remote, string_types) else remote.name
        pretty_print_notebook_diff(base_name, remote_name, a, d, config)

    return 0


def _build_arg_parser():
    """Creates an argument parser for the nbdiff command."""
    parser = argparse.ArgumentParser(
        description=_description,
        )
    add_generic_args(parser)
    add_diff_args(parser)
    add_diff_cli_args(parser)

    parser.add_argument(
        "base", help="The base notebook filename OR base git-revision.",
        nargs='?', default='HEAD',
    )
    parser.add_argument(
        "remote", help="The remote modified notebook filename OR remote git-revision.",
        nargs='?', default=None,
    )
    parser.add_argument(
        "paths", help="Filter diffs for git-revisions based on path",
        nargs='*', default=None,
    )

    parser.add_argument(
        '--out',
        default=None,
        help="if supplied, the diff is written to this file. "
             "Otherwise it is printed to the terminal.")

    return parser


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    setup_std_streams()
    arguments = _build_arg_parser().parse_args(args)
    return main_diff(arguments)


if __name__ == "__main__":
    sys.exit(main())
