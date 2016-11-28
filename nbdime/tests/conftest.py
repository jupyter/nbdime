# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

try:
    from unittest import mock
except ImportError:
    import mock

from pytest import fixture


@fixture
def nocolor(request):
    """Disable color printing for test"""
    import nbdime.prettyprint as pp
    patch = mock.patch.multiple(pp,
        ADD=pp.ADD.replace(pp.GREEN,''),
        REMOVE=pp.REMOVE.replace(pp.RED,''),
        INFO=pp.INFO.replace(pp.BLUE,''),
        RESET='',
        _git_diff_print_cmd=pp._git_diff_print_cmd.replace(' --color-words', ''),
    )
    patch.start()
    request.addfinalizer(patch.stop)
