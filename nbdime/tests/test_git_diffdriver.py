# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.



import io
import os
from os.path import join as pjoin
import sys
from unittest import mock

import pytest
from tornado import ioloop

from nbdime.vcs.git.diffdriver import main as gdd_main
from nbdime.prettyprint import file_timestamp
from nbdime.utils import locate_gitattributes

from .utils import WEB_TEST_TIMEOUT, call


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

expected_no_filter = """nbdiff {0} {1}
--- {0}  {2}
+++ {1}  {3}
## inserted before /cells/2:
+  code cell:
+    execution_count: 2
+    metadata (known keys):
+      collapsed: False
+    source:
+      x

## deleted /cells/3:
-  code cell:
-    execution_count: 2
-    metadata (known keys):
-      collapsed: False
-    source:
-      x

## inserted before /cells/5:
+  code cell:
+    metadata (known keys):
+      collapsed: False
+    source:
+      x

## deleted /cells/6:
-  code cell:
-    metadata (known keys):
-      collapsed: False
-    source:
-      x

"""

expected_strip_output_filter = """nbdiff {0} {1}
--- {0}  {2}
+++ {1}  {3}
## inserted before /cells/2:
+  code cell:
+    execution_count: 2
+    metadata (known keys):
+      collapsed: False
+    source:
+      x

## deleted /cells/3:
-  code cell:
-    execution_count: 2
-    metadata (known keys):
-      collapsed: False
-    source:
-      x
-    outputs:
-      output 0:
-        output_type: execute_result
-        execution_count: 2
-        data:
-          text/plain: 3

## replaced (type changed from int to NoneType) /cells/5/execution_count:
-  4
+  None

## deleted /cells/5/outputs/0:
-  output:
-    output_type: execute_result
-    execution_count: 4
-    data:
-      text/plain: 5

## replaced (type changed from NoneType to int) /cells/6/execution_count:
-  None
+  4

"""

expected_helper_filter = """nbdiff {0} {1}
--- {0}  {2}
+++ {1}  {3}
## inserted before /cells/2:
+  code cell:
+    execution_count: 2
+    metadata (known keys):
+      collapsed: False
+    source:
+      x

## deleted /cells/3:
-  code cell:
-    execution_count: 2
-    metadata (known keys):
-      collapsed: False
-    source:
-      x

## inserted before /cells/5:
+  code cell:
+    metadata (known keys):
+      collapsed: False
+    source:
+      x

## inserted before /cells/6:
+  raw cell:
+    id: filtered-cell
+    source:
+      nbdime test filter marker

## deleted /cells/6:
-  code cell:
-    metadata (known keys):
-      collapsed: False
-    source:
-      x

"""

def test_git_diff_driver(filespath, capsys, needs_git, reset_notebook_diff):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = pjoin(filespath, 'foo--1.ipynb')
    fn2 = pjoin(filespath, 'foo--2.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        '--no-color',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_output.format(fn1, fn2, t1, t2)


def test_git_diff_driver_flags(filespath, capsys, needs_git, reset_notebook_diff):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = pjoin(filespath, 'foo--1.ipynb')
    fn2 = pjoin(filespath, 'foo--2.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff', '-s',
        '--no-color',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_source_only.format(fn1, fn2, t1, t2)


def test_git_diff_driver_ignore_flags(filespath, capsys, needs_git, reset_notebook_diff):
    # Simulate a call from `git diff` to check basic driver functionality

    fn1 = pjoin(filespath, 'foo--1.ipynb')
    fn2 = pjoin(filespath, 'foo--2.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        '--no-color',
        '-O',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_source_only.format(fn1, fn2, t1, t2)



def _config_filter_driver(name, capsys):
    path = os.path.abspath(pjoin(os.path.dirname(__file__), 'filters', '%s.py' % name))
    base_cmd = '%s %s' % (sys.executable, path)
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tfilter=%s\n' % (name,))
    with capsys.disabled():
        call('git config --local --add filter.%s.clean "%s clean"' % (name, base_cmd))
        call('git config --local --add filter.%s.smudge "%s smudge"' % (name, base_cmd))


def test_git_diff_driver_noop_filter(git_repo, filespath, capsys, reset_notebook_diff):
    _config_filter_driver('noop', capsys)
    fn1 = pjoin(git_repo, 'diff.ipynb')
    fn2 = pjoin(filespath, 'src-and-output--1.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        '--use-filter',
        '--no-color',
        '-O',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_no_filter.format(fn1, fn2, t1, t2)


def test_git_diff_driver_strip_outputs_filter(git_repo, filespath, capsys, reset_notebook_diff):
    _config_filter_driver('strip_outputs', capsys)
    fn1 = pjoin(git_repo, 'diff.ipynb')
    fn2 = pjoin(filespath, 'src-and-output--1.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        '--use-filter',
        '--no-color',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_strip_output_filter.format(fn1, fn2, t1, t2)


def test_git_diff_driver_add_helper_filter(git_repo, filespath, capsys, reset_notebook_diff):
    _config_filter_driver('add_helper', capsys)
    fn1 = pjoin(git_repo, 'diff.ipynb')
    fn2 = pjoin(filespath, 'src-and-output--1.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        '--use-filter',
        '--no-color',
        '-O',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_helper_filter.format(fn1, fn2, t1, t2)


def test_git_diff_driver_no_filter_without_flag(git_repo, filespath, capsys, reset_notebook_diff):
    _config_filter_driver('add_helper', capsys)
    fn1 = pjoin(git_repo, 'diff.ipynb')
    fn2 = pjoin(filespath, 'src-and-output--1.ipynb')
    t1 = file_timestamp(fn1)
    t2 = file_timestamp(fn2)

    mock_argv = [
        '/mock/path/git-nbdiffdriver', 'diff',
        '--no-color',
        '-O',
        fn1,
        fn1, 'invalid_mock_checksum', '100644',
        fn2, 'invalid_mock_checksum', '100644']

    with mock.patch('sys.argv', mock_argv):
        r = gdd_main()
        assert r == 0
        cap_out = capsys.readouterr()[0]
        assert cap_out == expected_no_filter.format(fn1, fn2, t1, t2)


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_git_web_diff_driver(filespath, unique_port, reset_log, ioloop_patch, reset_notebook_diff):
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
