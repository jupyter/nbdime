# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

class NBDimeError(Exception):
    pass

class NBDiffFormatError(ValueError):
    pass

def error(msg):
    raise NBDimeError(msg)
