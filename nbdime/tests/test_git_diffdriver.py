
from __future__ import unicode_literals

import pytest
import mock
import os
from  os.path import join as pjoin

from nbdime.gitdiffdriver import main as gdd_main


# Expected output includes coloring characters
expected_output = """nbdiff {0} {1}
--- a: {0}
+++ b: {1}

patch a/cells/0/outputs/0/data/text/plain:
@@ -1 +1 @@
-6
\ No newline at end of file
+3
\ No newline at end of file
patch a/cells/0/source:
@@ -1,3 +1,3 @@
-def foe(x, y):
+def foo(x, y):
     return x + y
-foe(3, 2)
\ No newline at end of file
+foo(1, 2)
\ No newline at end of file
patch a/cells/1/source:
@@ -1,3 +1,3 @@
-def foo(x, y):
+def foe(x, y):
     return x * y
-foo(1, 2)
\ No newline at end of file
+foe(1, 2)
\ No newline at end of file
"""


def test_git_diff_driver(capsys):
    # Simulate a call from `git diff` to check basic driver functionality
    test_dir = os.path.abspath(os.path.dirname(__file__))
    mock_argv = ['/mock/path/git-nbdiffdriver', 'diff',
        pjoin(test_dir, 'files/foo-foe-1.ipynb'),
        pjoin(test_dir, 'files/foo-foe-1.ipynb'), 'invalid_mock_checksum', '100644',
        pjoin(test_dir, 'files/foo-foe-2.ipynb'), 'invalid_mock_checksum', '100644']
    import nbdime.prettyprint
    # Disable color printing for test
    nbdime.prettyprint._git_diff_print_cmd = \
        nbdime.prettyprint._git_diff_print_cmd.replace(' --color-words', '')
    with mock.patch('sys.argv', mock_argv):
        with pytest.raises(SystemExit) as cm:
            gdd_main()
        assert cm.value.code == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out  == expected_output.format(
            pjoin(test_dir, 'files/foo-foe-1.ipynb'),
            pjoin(test_dir, 'files/foo-foe-2.ipynb'))
