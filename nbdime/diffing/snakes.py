# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.
"""

import operator
from nbdime.diffing.seq_bruteforce import bruteforce_compute_snakes

__all__ = ["diff_notebooks"]


def compute_snakes(A, B, rect, compare):
    i0, j0, i1, j1 = rect

    # TODO: Implement this using difflib or recursive Myers or simpler
    # non-recursive Myers algorithm without the middle snake stuff

    # snakes = [(i, j, n)]
    snakes = bruteforce_compute_snakes(A[i0:i1], B[j0:j1], compare)
    snakes = [(i+i0, j+j0, n) for (i, j, n) in snakes]

    assert all(compare(A[i+k], B[j+k]) for (i, j, n) in snakes for k in range(n))
    return snakes


def compute_snakes_multilevel(A, B, rect, predicates, level):
    """Compute snakes using a multilevel multi-predicate algorithm.

    TODO: Document this algorithm.
    """
    compare = predicates[level]
    snakes = compute_snakes(A, B, rect, compare)
    if level == 0:
        return snakes
    newsnakes = [(0, 0, 0)]
    i0, j0, i1, j1 = rect
    for snake in snakes + [(i1, j1, 0)]:
        i, j, n = snake
        if i > i0 and j > j0:
            newsnakes += compute_snakes_multilevel(A, B, (i0, j0, i, j), predicates, level-1)
        if n > 0:
            if newsnakes[-1][0] == i and newsnakes[-1][1] == j:
                snake = newsnakes[-1]
                newsnakes[-1] = (snake[0], snake[1], snake[2] + n)
            else:
                newsnakes.append(snake)
        i0 = i + n
        j0 = j + n
    if newsnakes[0][2] == 0:
        newsnakes.pop(0)
    return newsnakes
