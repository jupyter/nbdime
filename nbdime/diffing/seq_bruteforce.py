# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import operator
import numpy as np
from .lcs import diff_from_lcs

__all__ = ["diff_sequence_bruteforce"]

def bruteforce_compare_grid(A, B, compare=operator.__eq__):
    "Brute force compute grid G[i, j] == compare(A[i], B[j])."
    N, M = len(A), len(B)
    G = np.empty((N, M), dtype=int)
    for i in range(N):
        for j in range(M):
            G[i, j] = compare(A[i], B[j])
    return G

def bruteforce_llcs_grid(G):
    "Brute force compute grid R[x, y] == llcs(A[:x], B[:y]), given G[i,j] = compare(A[i], B[j])."
    N, M = G.shape
    R = np.zeros((N+1, M+1), dtype=int)
    for x in range(1, N+1):
        for y in range(1, M+1):
            if G[x-1, y-1]:
                R[x, y] = R[x-1, y-1] + 1
            else:
                R[x, y] = max(R[x-1, y], R[x, y-1])
    return R

def bruteforce_lcs_indices(A, B, G, R, compare=operator.__eq__):
    """Brute force compute the lcs of A and B.

    Returns two lists (A_indices, B_indices) with length == llcs(A, B),
    such that lcs(A, B) == A[A_indices] == B[B_indices].
    """
    N, M = len(A), len(B)
    A_indices = []
    B_indices = []
    x = N
    y = M
    while x > 0 and y > 0:
        if G[x-1, y-1]:
            assert R[x, y] == R[x-1, y-1] + 1
            x -= 1
            y -= 1
            A_indices.append(x)
            B_indices.append(y)
        elif R[x, y] == R[x-1, y]:
            x -= 1
        else:
            assert R[x, y] == R[x, y-1]
            y -= 1
    A_indices.reverse()
    B_indices.reverse()
    return A_indices, B_indices

def diff_sequence_bruteforce(A, B, compare=operator.__eq__):
    """Compute the diff of A and B using expensive brute force O(MN) algorithms."""
    G = bruteforce_compare_grid(A, B, compare)
    R = bruteforce_llcs_grid(G)
    A_indices, B_indices = bruteforce_lcs_indices(A, B, G, R, compare)
    return diff_from_lcs(A, B, A_indices, B_indices)
