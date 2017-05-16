# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

import os
from os.path import join as pjoin

import mock
import pytest
from tornado import ioloop

from nbdime.vcs.git.diffdriver import main as gdd_main
from nbdime.prettyprint import file_timestamp

from .utils import WEB_TEST_TIMEOUT


# Expected output includes coloring characters
expected_output = """nbdiff {0} {1}
--- {0}  {2}
+++ {1}  {3}
## modified /cells/0/outputs/0/data/text/plain:
-  6
+  3

## modified /cells/0/source:
@@ -1,3 +1,3 @@
-def foe(x, y):
+def foo(x, y):
     return x + y
-foe(3, 2)
+foo(1, 2)

## modified /cells/1/source:
@@ -1,3 +1,3 @@
-def foo(x, y):
+def foe(x, y):
     return x * y
-foo(1, 2)
+foe(1, 2)

"""

expected_source_only = """nbdiff {0} {1}
--- {0}  {2}
+++ {1}  {3}
## modified /cells/0/source:
@@ -1,3 +1,3 @@
-def foe(x, y):
+def foo(x, y):
     return x + y
-foe(3, 2)
+foo(1, 2)

## modified /cells/1/source:
@@ -1,3 +1,3 @@
-def foo(x, y):
+def foe(x, y):
     return x * y
-foo(1, 2)
+foe(1, 2)

"""


def test_git_diff_driver(filespath, capsys, nocolor, needs_git):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = pjoin(filespath, 'foo--1.ipynb')
    fn2 = pjoin(filespath, 'foo--2.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_output.format(fn1, fn2, t1, t2)


def test_git_diff_driver_flags(filespath, capsys, nocolor, needs_git, reset_diff_targets):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = pjoin(filespath, 'foo--1.ipynb')
    fn2 = pjoin(filespath, 'foo--2.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff', '-s',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_source_only.format(fn1, fn2, t1, t2)


def test_git_diff_driver_ignore_flags(filespath, capsys, nocolor, needs_git, reset_diff_targets):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = pjoin(filespath, 'foo--1.ipynb')
    fn2 = pjoin(filespath, 'foo--2.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff', '-O',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_source_only.format(fn1, fn2, t1, t2)


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_git_web_diff_driver(filespath, unique_port):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = os.path.join(filespath, 'foo--1.ipynb')
    fn2 = os.path.join(filespath, 'foo--2.ipynb')

    loop = ioloop.IOLoop.current()
    loop.call_later(0, loop.stop)

    mock_argv = [
        'git-nbdiffdriver', 'webdiff',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644',
        '--browser=disabled', '--port=%i' % unique_port]

    with mock.patch('sys.argv', mock_argv):
        # This simply checks that the function returns 0,
        # but assumes that the function is routed to the web
        # diff entrypoint
        r = gdd_main()
        assert r == 0
