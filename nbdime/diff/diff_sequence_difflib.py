# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from difflib import SequenceMatcher

__all__ = ["diff_sequence_difflib"]

def opcodes_to_diff(a, b, opcodes):
    "Convert difflib opcodes to nbdime diff format."
    d = []
    for opcode in opcodes:
        action, abegin, aend, bbegin, bend = opcode
        asize = aend - abegin
        bsize = bend - bbegin
        if action == "equal":
            pass
        elif action == "replace":
            if asize == bsize:
                if asize == 1:
                    d.append([':', abegin, b[bbegin]])
                else:
                    d.append(['::', abegin, b[bbegin:bend]])
            else:
                if asize == 1:
                    d.append(['-', abegin])
                else:
                    d.append(['--', abegin, asize])
                if bsize == 1:
                    d.append(['+', abegin, b[bbegin]])
                else:
                    d.append(['++', abegin, b[bbegin:bend]])
        elif action == "insert":
            if bsize == 1:
                d.append(["+", abegin, b[bbegin]])
            else:
                d.append(["++", abegin, b[bbegin:bend]])
        elif action == "delete":
            if asize == 1:
                d.append(['-', abegin])
            else:
                d.append(['--', abegin, asize])
        else:
            raise RuntimeError("Unknown action {}".format(action))
    return d

def diff_sequence_difflib(a, b):
    """Compute the diff of two sequences.

    This implementation uses SequenceMatcher from the builtin Python difflib.

    By the difflib documentation this should work for sequences of
    hashable objects, i.e. the elements of the sequences are only
    compared for full equality. Therefore this function does not take
    a custom compare function like the other diff_sequence_* variants.
    """
    s = SequenceMatcher(None, a, b, autojunk=False)
    return opcodes_to_diff(a, b, s.get_opcodes())
