# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import nbformat

def merge(base, local, remote):
    # FIXME: Implement merge
    return None

def merge_notebooks(base, local, remote):
    # FIXME: Implement merge
    merged = merge(base, local, remote)
    return nbformat.from_dict(merged)
