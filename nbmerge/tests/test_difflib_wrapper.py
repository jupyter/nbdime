
from nbmerge.diff.patch import patch

import copy
from difflib import SequenceMatcher

def diff_sequence(a, b, include_equal=False):
    """Diff lines with index tracking.

    TODO: Document return format here, it's not quite standard.
    """

    # TODO: Make this easy configurable?

    # TODO: Compare to my notebook diff prototype for curiosity. How does it perform?

    diff = []
    s = SequenceMatcher(lambda x: False, a, b)
    for opcode in s.get_opcodes():
        action, abegin, aend, bbegin, bend = opcode
        if action == "replace":
            if bend - bbegin == aend - abegin:
                diff.extend(['::', abegin, b[bbegin:bend]])
            else:
                diff.append(['--', abegin, aend-abegin])
                diff.extend(['++', abegin, b[bbegin:bend]])
        elif action == "equal":
            if include_equal:
                diff.extend(['=', i, i-abegin+bbegin] for i in range(abegin, aend))
        elif action == "insert":
            diff.extend(['+', abegin, j] for j in range(bbegin, bend))
        elif action == "delete":
            diff.extend(['-', i] for i in range(abegin, aend))
        else:
            raise RuntimeError("Unknown action {}".format(action))
    return diff


def test_difflib_wrapper():

    assert patch(a, diff_sequence(a, b)) == b
