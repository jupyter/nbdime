try:
    from unittest import mock
except ImportError:
    import mock

from pytest import fixture

import nbdime.prettyprint as pp

@fixture(autouse=True)
def nocolor(request):
    """Disable color printing for test"""
    patch = mock.patch.multiple(pp,
        ADD='+ ', REMOVE='- ', RESET='',
        _git_diff_print_cmd=pp._git_diff_print_cmd.replace(' --color-words', ''),
    )
    patch.start()
    request.addfinalizer(patch.stop)

@fixture
def noindent(request):
    """Ensure indent is False"""
    patch = mock.patch.multiple(pp, with_indent=False)
    patch.start()
    request.addfinalizer(patch.stop)

@fixture
def indent(request):
    """Ensure indent is True"""
    patch = mock.patch.multiple(pp, with_indent=True)
    patch.start()
    request.addfinalizer(patch.stop)
