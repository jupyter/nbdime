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
        ADD='+', REMOVE='-', RESET='',
        _git_diff_print_cmd=pp._git_diff_print_cmd.replace(' --color-words', ''),
    )
    patch.start()
    request.addfinalizer(patch.stop)

@fixture
def noindent(request):
    """Ensure indent is False"""
    import nbdime.prettyprint as pp
    patch = mock.patch.multiple(pp, with_indent=False)
    patch.start()
    request.addfinalizer(patch.stop)

@fixture
def indent(request):
    """Ensure indent is True"""
    import nbdime.prettyprint as pp
    patch = mock.patch.multiple(pp, with_indent=True)
    patch.start()
    request.addfinalizer(patch.stop)
