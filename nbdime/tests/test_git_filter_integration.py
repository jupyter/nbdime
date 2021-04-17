
import io
import os
from io import StringIO
from subprocess import CalledProcessError

import nbformat

from nbdime.vcs.git.filter_integration import (
    interrogate_filter, apply_possible_filter, get_clean_filter_cmd)
from nbdime.utils import locate_gitattributes

from .utils import call

pjoin = os.path.join


def test_interrogate_filter_no_repo(filespath):
    assert interrogate_filter(pjoin(filespath, 'foo--1.ipynb')) is None


def test_interrogate_filter_blank(git_repo):
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tfilter=\n')

    attr = interrogate_filter(pjoin(git_repo, 'foo--1.ipynb'))

    assert attr is None


def test_interrogate_filter_unspecified(git_repo):
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\t!filter\n')

    attr = interrogate_filter(pjoin(git_repo, 'foo--1.ipynb'))

    assert attr is None


def test_interrogate_filter_value(git_repo):
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tfilter=myfilter\n')

    attr = interrogate_filter(pjoin(git_repo, 'diff.ipynb'))

    assert attr == 'myfilter'


def test_interrogate_filter_set(git_repo):
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tfilter\n')

    attr = interrogate_filter(pjoin(git_repo, 'diff.ipynb'))

    assert attr is None


def test_interrogate_filter_unset(git_repo):
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\t-filter\n')

    attr = interrogate_filter(pjoin(git_repo, 'diff.ipynb'))

    assert attr is None


def test_filter_cmd_invalid_filter():
    assert get_clean_filter_cmd('mynonexistantfilter') is None


def test_filter_cmd_valid_filter(git_repo):
    call('git config --local --add filter.myfilter.clean "testcmd --arg"')
    assert get_clean_filter_cmd('myfilter') == 'testcmd --arg'



def test_apply_filter_no_repo(filespath):
    path = pjoin(filespath, 'foo--1.ipynb')
    assert apply_possible_filter(path) == path


def test_apply_filter_no_filter(git_repo):
    path = pjoin(git_repo, 'diff.ipynb')
    assert apply_possible_filter(path) == path


def test_apply_filter_invalid_filter(git_repo):
    path = pjoin(git_repo, 'diff.ipynb')
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tfilter=myfilter\n')
    assert apply_possible_filter(path) == path


def test_apply_filter_valid_filter(git_repo):
    filter_cmd = 'findstr x*' if os.name == 'nt' else 'cat'
    path = pjoin(git_repo, 'diff.ipynb')
    gitattr = locate_gitattributes()
    with io.open(gitattr, 'a', encoding="utf8") as f:
        f.write(u'\n*.ipynb\tfilter=myfilter\n')
    call('git config --local --add filter.myfilter.clean "%s"' % filter_cmd)
    f = apply_possible_filter(path)
    assert isinstance(f, StringIO)
    # Read validates notebook:
    nbformat.validate(nbformat.read(f, as_version=4))
