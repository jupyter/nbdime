# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals


class NBDimeError(Exception):
    pass


class NBDiffFormatError(ValueError):
    pass


def error(msg):
    raise NBDimeError(msg)
