# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import logging


class NBDiffFormatError(ValueError):
    pass


def init_logging():
    """Sets up logging for nbdime entry points.

    Call this in all entry points (if __name__ == "__main__").
    Sets the log level for all nbdime loggers to `level`,
    unless `level` is given as `None`.
    """
    logging.basicConfig()
