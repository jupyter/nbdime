# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


def test_pkg_import_no_webapp():
    # Test that importing nbdime does not import webapp
    # as this is an expensive import
    import nbdime
    import sys
    assert 'ndime.webapp' not in sys.modules
