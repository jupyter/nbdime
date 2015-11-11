
from nbmerge.diff.patch import patch

import copy
from difflib import SequenceMatcher

def opcodes_to_diff(a, b, opcodes):
    "Convert difflib opcodes to nbmerge diff format."
    diff = []
    for opcode in opcodes:
        action, abegin, aend, bbegin, bend = opcode
        asize = aend - abegin
        bsize = bend - bbegin
        if action == "equal":
            pass
        elif action == "replace":
            if asize == bsize:
                if asize == 1:
                    diff.append([':', abegin, b[bbegin]])
                else:
                    diff.append(['::', abegin, b[bbegin:bend]])
            else:
                if asize == 1:
                    diff.append(['-', abegin])
                else:
                    diff.append(['--', abegin, asize])
                if bsize == 1:
                    diff.append(['+', abegin, b[bbegin]])
                else:
                    diff.append(['++', abegin, b[bbegin:bend]])
        elif action == "insert":
            if bsize == 1:
                diff.append(["+", abegin, b[bbegin]])
            else:
                diff.append(["++", abegin, b[bbegin:bend]])
        elif action == "delete":
            if asize == 1:
                diff.append(['-', abegin])
            else:
                diff.append(['--', abegin, asize])
        else:
            raise RuntimeError("Unknown action {}".format(action))
    return diff

def diff_sequence(a, b):
    """Compute a diff of two sequences.

    Current implementation uses SequenceMatcher from the builtin Python
    difflib. By the difflib documentation this should work for sequences
    of hashable objects, i.e. the elements of the sequences are only
    compared for full equality.
    """
    s = SequenceMatcher(lambda x: False, a, b)
    return opcodes_to_diff(a, b, s.get_opcodes())

def test_difflib_wrapper():
    a = """\
    def f(a, b):
        c = a * b
        return c

    def g(x):
        y = x**2
        return y
    """.splitlines()

    b = []
    assert patch(a, diff_sequence(a, b)) == b
    assert patch(b, diff_sequence(b, a)) == a

    for i in range(len(a)+1):
        for j in range(len(a)+1):
            for k in range(len(a)+1):
                for l in range(len(a)+1):
                    b = a[i:j] + a[k:l]
                    assert patch(a, diff_sequence(a, b)) == b
                    assert patch(b, diff_sequence(b, a)) == a

    #print("\n".join(map(repr, diff_sequence(a, b))))
