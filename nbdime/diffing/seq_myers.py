# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import operator

from ..diff_format import SequenceDiffBuilder

__all__ = ["diff_sequence_myers"]



# Set to true to enable additional assertions, array access checking, and printouts
DEBUGGING = False
#import pdb


class DebuggingArray(object):
    "Debugging tool to capture array accesses."
    def __init__(self, n, name):
        print("Alloc %s[%d]" % (name, n))
        self.a = [None]*n
        self.w = [0]*n
        self.name = name

    def __getitem__(self, i):
        if not self.w[i]:
            raise RuntimeError("Trying to read unwritten location in array!")
        print("    %d <- %s[%d]" % (self.a[i], self.name, i))
        return self.a[i]

    def __setitem__(self, i, v):
        if self.w[i]:
            print("    %s[%d] <- %d (was: %d)" % (self.name, i, v, self.a[i]))
        else:
            print("    %s[%d] <- %d (first access)" % (self.name, i, v))
        self.w[i] = 1
        self.a[i] = v
        return v


def alloc_V_array(MAX, name):
    # Size of array should be big enough for MAX edits,
    # and thus indexing from V[V0-D] to V[V0+D], V0=MAX
    n = 2 * MAX + 1

    # Not initializing V with zeros, if the algorithms access uninitialized values that's a bug
    V = [None] * n

    # Enabling this allows debugging accesses to uninitialized values
    if DEBUGGING:
        V = DebuggingArray(n, name)

    return V


def find_middle_snake(A, B, compare=operator.__eq__):
    N = len(A)
    M = len(B)
    delta = N - M
    odd = delta % 2 == 1
    even = not odd

    # Allocate uninitialized array with minimal integer size needed
    # V is indexed from -MAX to +MAX in the algorithm,
    # here indexing using V[V0 + i] to map to 0-based indices
    V0 = N + M
    Vf = alloc_V_array(V0, "Vf")
    Vr = alloc_V_array(V0, "Vr")
    # Seed for first iterations:
    Vf[V0 + 1] = 0
    Vr[V0 - 1] = N

    # For an increasing number of edits
    if DEBUGGING:
        print("A, B =", (A, B))
        print("Iterating D to ", V0 + 1)
    for D in range(V0 + 1):
        if DEBUGGING:
            print("Forward", D)
        # Forward search along k-diagonals
        for k in range(-D, D + 1, 2):
            if DEBUGGING:
                print("  k:", k)

            # Find the end of the furthest reaching forward D-path in diagonal k
            x, y, u, v = find_forward_path(A, B, Vf, V0, D, k, compare)
            if DEBUGGING:
                print("    xyuv:", x, y, u, v)

            Vf[V0 + k] = u

            # Look for overlap with reverse search
            if odd and D > 0 and (-(D - 1) <= k - delta <= (D - 1)):
                # Check if the path overlaps the furthest reaching reverse D-1-path in diagonal k
                if Vr[V0 + k - delta] <= Vf[V0 + k]:
                    # Length of the SES
                    ses = 2 * D - 1
                    # The last snake of the forward path is the middle snake
                    return ses, x, y, u, v

        if DEBUGGING:
            print("Reverse", D)
        # Reverse search along k-diagonals
        #for k in range(-D, D+1, 2):
        for k in range(D, -D - 1, -2):
            if DEBUGGING:
                print("  k:", k)

            # Find the end of the furthest reaching reverse D-path in diagonal k+delta
            x, y, u, v = find_reverse_path(A, B, Vr, V0, D, k, delta, compare)
            if DEBUGGING:
                print("    xyuv:", x, y, u, v)

            Vr[V0 + k] = x

            # Look for overlap with forward search
            if even and (-D <= k + delta <= D):
                # Check if the path overlaps the furthest reaching forward D-path in diagonal k+delta
                if Vr[V0 + k] <= Vf[V0 + k + delta]:
                    # Length of the SES
                    ses = 2*D
                    # The last snake of the reverse path is the middle snake
                    return ses, x, y, u, v

    raise RuntimeError("Failed to find middle snake!")


def find_forward_path(A, B, V, V0, D, k, compare=operator.__eq__):
    "The greedy LCS/SES algorithm from Fig. 2 of Myers' article."
    N, M = len(A), len(B)

    if k == -D or k != D and V[V0 + k - 1] < V[V0 + k + 1]:
        # Coming from diagonal k+1, the diagonal above k, so keeping x
        x = V[V0 + k + 1]
    else:
        # Coming from diagonal k-1, the diagonal to the left of k, so incrementing x
        x = V[V0 + k - 1] + 1
    # Forward lines are centered around x-y=0
    y = x - k

    x0 = x
    y0 = y

    # Compare sequence elements along k-diagonal
    while x < N and y < M and compare(A[x], B[y]):
        if DEBUGGING:
            print('Identical:', x, y, A[x])
        x += 1
        y += 1

    if DEBUGGING:
        assert x0 == N or y0 == M or (x - x0) == 0 or compare(A[x0], B[y0])
        assert x >= N or y >= M or not compare(A[x], B[y])
        for i in range(x-x0):
            assert compare(A[x0 + i], B[y0 + i])

    # The forward snake covers [x0,x) [y0,y)
    return x0, y0, x, y


def find_reverse_path(A, B, V, V0, D, k, delta, compare=operator.__eq__):
    "Reverse variant of the greedy LCS/SES algorithm from Fig. 2 of Myers' article."
    N, M = len(A), len(B)
    delta = N - M

    if k == D or k != -D and V[V0 + k - 1] < V[V0 + k + 1]:
        # Coming from diagonal k-1, the diagonal below k, so keeping x
        x = V[V0 + k - 1]
    else:
        # Coming from diagonal k+1, the diagonal to the right of k, so decrementing x
        x = V[V0 + k + 1] - 1
    #if k == -D or k != D and V[V0+k-1] < V[V0+k+1]:
    #    # Coming from diagonal k+1, the diagonal to the right of k, so decrementing x
    #    x = V[V0+k+1] - 1
    #else:
    #    # Coming from diagonal k-1, the diagonal below k, so keeping x
    #    x = V[V0+k-1]
    # Reverse lines are centered around x-y=delta
    y = x - k - delta

    x0 = x
    y0 = y

    # Compare sequence elements along k-diagonal
    # while x >= 0 and y >= 0 and compare(A[x], B[y]):
    while x >= 1 and y >= 1 and compare(A[x-1], B[y-1]):
        if DEBUGGING:
            print('Identical:', x-1, y-1, A[x-1])
        x -= 1
        y -= 1

    if False and DEBUGGING:
        # FIXME
        assert x0 < 0 or y0 < 0 or (x0-x) == 0 or compare(A[x0], B[y0])
        assert x < 0 or y < 0 or not compare(A[x], B[y])
        for i in range(x0-x):
            assert compare(A[x0-i], B[y0-i])

    #FIXME
    #For a nonzero snake well inside domain we have that:
    #A[x0-2] == B[y0-2]
    #A[x-2] != B[y-2]
    # The reverse snake covers (x,x0] (y,y0]

    # The forward snake covers (x,x0] (y,y0]
    return x, y, x0, y0 # FIXME: Reconsider this


def myers_ses(A, B, compare=operator.__eq__):
    "Yield edit operations of the see of A and B."
    N = len(A)
    M = len(B)
    if N and M:
        # Find the middle snake. The middle snake is a sequence
        # of 0 or more diagonals where
        D, x, y, u, v = find_middle_snake(A, B, compare)
        n = u - x
        assert v - y == n
        assert x - y == u - v

        if DEBUGGING:
            print('Middle snake:', D, x, y, u, v)
            for i in range(n):
                assert compare(A[x+i], B[y+i])

        if D > 1:
            # Yield ses of the upper/left corner rectangle (recurse)
            if DEBUGGING:
                print('Recursing upper-left:', 0, 0, x, y)
            for s in myers_ses(A[:x], B[:y]):
                yield s
            # Yield the middle snake
            for i in range(n):
                yield 0
            # Yield ses of the lower/right corner rectangle (recurse)
            if DEBUGGING:
                print('Recursing lower-right:', x + n, y + n, len(A), len(B))
            for s in myers_ses(A[x + n:], B[y + n:]):
                yield s
        else:
            # If only 0 or 1 edit operation is needed,
            # we do not need to recurse
            for i in range(min(x, y)):
                yield 0
            if x > y:
                yield -1
            elif y > x:
                yield 1
            # Yield the middle snake
            for i in range(n):
                yield 0
    elif N:
        for s in A:
            yield -1
    elif M:
        for s in B:
            yield 1


def diff_from_es(A, B, edit_gen):
    """Compute the diff of A and B, given an edit string."""
    di = SequenceDiffBuilder()
    # x,y = how many symbols we have consumed from A and B
    x = 0
    y = 0
    prev_op = None
    prev_len = 0
    for op in edit_gen:
        if op != prev_op:
            # Finish previous op
            if prev_op == -1:
                di.removerange(x, prev_len)
                x += prev_len
            elif prev_op == 1:
                di.addrange(x, B[y : y + prev_len])
                y += prev_len
            prev_op = op
            prev_len = 1
        else:
            prev_len += 1

        if op == 0:
            x += 1
            y += 1

    if prev_op == -1:
        di.removerange(x, prev_len)
    elif prev_op == 1:
        di.addrange(x, B[y : y + prev_len])
    return di.validated()

def diff_sequence_myers(A, B, compare=operator.__eq__):
    """Compute the diff of A and B using Myers' O(ND) algorithm."""
    ses_gen = myers_ses(A, B, compare)
    return diff_from_es(A, B, ses_gen)
