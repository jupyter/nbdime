
from __future__ import unicode_literals

import pytest
import unittest
import os
from  os.path import join as pjoin

from nbdime.gitdiffdriver import main as gdd_main


# Expected output includes coloring characters
expected_output = """nbdiff {0} {1}
--- a: {0}
+++ b: {1}

patch a/cells/0/outputs/0/data/text/plain:
\x1b[36m@@ -1 +1 @@\x1b[m
\x1b[31m6\x1b[m\x1b[32m3\x1b[m
patch a/cells/0/source:
\x1b[36m@@ -1,3 +1,3 @@\x1b[m
def \x1b[31mfoe(x,\x1b[m\x1b[32mfoo(x,\x1b[m y):
    return x + y\x1b[m
\x1b[31mfoe(3,\x1b[m\x1b[32mfoo(1,\x1b[m 2)
patch a/cells/1/source:
\x1b[36m@@ -1,3 +1,3 @@\x1b[m
def \x1b[31mfoo(x,\x1b[m\x1b[32mfoe(x,\x1b[m y):
    return x * y\x1b[m
\x1b[31mfoo(1,\x1b[m\x1b[32mfoe(1,\x1b[m 2)
"""


def test_git_diff_driver(capsys):
    # Simulate a call from `git diff` to check basic driver functionality
    test_dir = os.path.abspath(os.path.dirname(__file__))
    mock_argv = ['/mock/path/git-nbdiffdriver', 'diff',
        pjoin(test_dir, 'files/foo-foe-1.ipynb'),
        pjoin(test_dir, 'files/foo-foe-1.ipynb'), 'invalid_mock_checksum', '100644',
        pjoin(test_dir, 'files/foo-foe-2.ipynb'), 'invalid_mock_checksum', '100644']
    with unittest.mock.patch('sys.argv', mock_argv):
        with pytest.raises(SystemExit) as cm:
            gdd_main()
        assert cm.value.code == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out  == expected_output.format(
            pjoin(test_dir, 'files/foo-foe-1.ipynb'),
            pjoin(test_dir, 'files/foo-foe-2.ipynb'))
