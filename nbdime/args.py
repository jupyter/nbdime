# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import argparse
import logging
import os

from ._version import __version__
from .log import init_logging, set_nbdime_log_level

class LogLevelAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        level = getattr(logging, values)
        init_logging(level=level)
        set_nbdime_log_level(level)

def add_generic_args(parser):
    """Adds a set of arguments common to all nbdime commands.
    """
    parser.add_argument(
        '--version',
        action="version",
        version="%(prog)s " + __version__)
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        help="Set the log level by name.",
        action=LogLevelAction,
    )


def add_web_args(parser, default_port=8888):
    """Adds a set of arguments common to all commands that show a web gui.
    """
    port_help = (
        "specify the port you want the server to run on. Default is %d%s." % (
            default_port, " (random)" if default_port == 0 else ""
        ))
    parser.add_argument(
        '-p', '--port',
        default=default_port,
        type=int,
        help=port_help)
    parser.add_argument(
        '-b', '--browser',
        default=None,
        type=str,
        help="specify the browser to use, to override the system default.")
    cwd = os.path.abspath(os.path.curdir)
    parser.add_argument(
        '-w', '--workdirectory',
        default=cwd,
        help="specify the working directory you want "
             "the server to run from. Default is the "
             "actual cwd at program start.")


def add_diff_args(parser):
    """Adds a set of arguments for commands that perform diffs.

    Note:
        Merge applications also performs diff operations to compute
        the merge, so these arguments should also be included there.
    """
    # TODO: Add diff strategy options that are reusable for the
    # merge command here

    # TODO: Define sensible strategy variables and implement
    #parser.add_argument('-d', '--diff-strategy',
    #                    default="default", choices=("foo", "bar"),
    #                    help="specify the diff strategy to use.")
    pass


def add_merge_args(parser):
    """Adds a set of arguments for commands that perform merges.
    """
    from .merging.notebooks import cli_conflict_strategies
    parser.add_argument(
        '-m', '--merge-strategy',
        default="inline",
        choices=cli_conflict_strategies,
        help="Specify the merge strategy to use.")
    parser.add_argument(
        '--input-strategy',
        default=None,
        choices=cli_conflict_strategies,
        help="Specify the merge strategy to use for inputs "
             "(overrides 'merge-strategy' for inputs).")
    parser.add_argument(
        '--output-strategy',
        default=None,
        choices=cli_conflict_strategies,
        help="Specify the merge strategy to use for outputs "
             "(overrides 'merge-strategy' for outputs).")
    parser.add_argument(
        '--no-ignore-transients',
        dest='ignore_transients',
        action="store_false",
        default=True,
        help="Disallow deletion of transient data such as outputs and "
             "execution counts in order to resolve conflicts.")


def add_filename_args(parser, names):
    """Add the base, local, remote, and merged positional arguments.

    Helps getting consistent doc strings.
    """
    helps = {
        "notebook": "The notebook filename.",
        "base":   "The base notebook filename.",
        "local":  "The local modified notebook filename.",
        "remote": "The remote modified notebook filename.",
        "merged": "The merge result notebook filename.",
        "patch":  "The patch filename, output from nbdiff.",
        }
    for name in names:
        parser.add_argument(name, help=helps[name])
