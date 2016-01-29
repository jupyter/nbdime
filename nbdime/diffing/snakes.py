# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.
"""

from ..diff_format import SequenceDiff
from .seq_bruteforce import bruteforce_compute_snakes
from .generic import diff

__all__ = ["diff_sequence_multilevel"]


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


def compute_diff_from_snakes(a, b, snakes, diff_single_item=diff):
    # Compute diff from snakes
    di = SequenceDiff()
    i0, j0, i1, j1 = 0, 0, len(a), len(b)
    for i, j, n in snakes + [(i1, j1, 0)]:
        if i > i0:
            di.remove(i0, i-i0)
        if j > j0:
            di.add(i0, b[j0:j])
        for k in range(n):
            cd = diff_single_item(a[i + k], b[j + k])
            if cd:
                di.patch(i+k, cd)
        # Update corner offsets for next rectangle
        i0, j0 = i+n, j+n
    return di.diff  # XXX


def diff_sequence_multilevel(a, b, predicates, subdiff=diff):
    # Invoke multilevel snake computation algorithm
    level = len(predicates) - 1
    rect = (0, 0, len(a), len(b))
    snakes = compute_snakes_multilevel(a, b, rect, predicates, level)
    return compute_diff_from_snakes(a, b, snakes, subdiff)
