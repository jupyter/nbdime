# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import json
import logging
import os
from pprint import pprint
from subprocess import CalledProcessError, check_call
import sys
import time

import pytest
import requests
from tornado.httputil import url_concat

import nbformat

from .utils import (
    assert_clean_exit, get_output, call, WEB_TEST_TIMEOUT,
    write_local_hg_config, wait_up
)

import nbdime
from nbdime.args import process_exclusive_ignorables
from nbdime.diffing.notebooks import notebook_differs
from nbdime.nbshowapp import main_show
from nbdime.nbdiffapp import main_diff
from nbdime.nbmergeapp import main_merge
from nbdime.__main__ import main_dispatch
from nbdime import (
    nbshowapp,
    nbdiffapp,
    nbmergeapp,
    nbpatchapp,
)
from nbdime.vcs.git import (
    diffdriver as gitdiffdriver,
    difftool as gitdifftool,
    mergedriver as gitmergedriver,
    mergetool as gitmergetool,
)
from nbdime.vcs.hg import (
    diff as hgdiff,
    diffweb as hgdiffweb,
    merge as hgmerge,
    mergeweb as hgmergeweb,
)
from nbdime.utils import EXPLICIT_MISSING_FILE


def test_nbshow_app(filespath, capsys):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")

    args = nbshowapp._build_arg_parser().parse_args([afn, '--log-level=CRITICAL'])
    process_exclusive_ignorables(
        args,
        ('sources', 'outputs', 'attachments', 'metadata', 'id', 'details'))
    assert 0 == main_show(args)
    assert args.log_level == 'CRITICAL'
    assert nbdime.log.logger.level == logging.CRITICAL


def test_nbpatch_app(capsys, filespath):
    # this entrypoint is not exported,
    # but exercise it anyway
    bfn = os.path.join(filespath, "multilevel-test-base.ipynb")
    dfn = os.path.join(filespath, "multilevel-test-base-local-diff.json")
    assert 0 == nbpatchapp.main([bfn, dfn])


def test_nbdiff_app(filespath):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    # When filename is omitted, will print to console instead
    # dfn = ""  # os.path.join(filespath, "multilevel-test-local-diff.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--log-level=WARN'])
    assert 0 == main_diff(args)
    assert args.log_level == 'WARN'
    assert nbdime.log.logger.level == logging.WARN


def test_nbdiff_app_null_file(filespath):
    fn = os.path.join(filespath, "multilevel-test-base.ipynb")

    args = nbdiffapp._build_arg_parser().parse_args([fn, EXPLICIT_MISSING_FILE])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args([EXPLICIT_MISSING_FILE, fn])
    assert 0 == main_diff(args)


def test_nbdiff_app_gitrefs(git_repo2):
    args = nbdiffapp._build_arg_parser().parse_args(['local', 'remote'])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args(['local', 'remote', 'sub/subfile.ipynb'])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args(['local', 'remote', 'sub/subfile.ipynb', 'diff.ipynb'])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args(['local', 'sub/subfile.ipynb', 'diff.ipynb'])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args(['sub/subfile.ipynb'])
    assert 0 == main_diff(args)

    args = nbdiffapp._build_arg_parser().parse_args([])
    assert 0 == main_diff(args)


def test_nbdiff_app_unicode_safe(filespath):
    afn = os.path.join(filespath, "unicode--1.ipynb")
    bfn = os.path.join(filespath, "unicode--2.ipynb")
    env = os.environ.copy()
    env['LC_ALL'] = 'C'
    env.pop('PYTHONIOENCODING', None)
    check_call([sys.executable, '-m', 'nbdime.nbdiffapp', afn, bfn], env=env)


def test_nbdiff_app_only_source(filespath, tmpdir, reset_notebook_diff):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")
    dfn = os.path.join(tmpdir.dirname, "diff_output.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--out', dfn, '-s'])
    assert 0 == main_diff(args)
    with io.open(dfn) as df:
        diff = json.load(df)
    for key in ('cells', 1, 'source'):
        assert len(diff) == 1
        assert diff[0]['key'] == key
        assert diff[0]['op'] == 'patch'
        diff = diff[0]['diff']


def test_nbdiff_app_ignore_source(filespath, tmpdir, reset_notebook_diff):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")
    dfn = os.path.join(tmpdir.dirname, "diff_output.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--out', dfn, '-S'])
    assert 0 == main_diff(args)
    with io.open(dfn) as df:
        diff = json.load(df)
    for key in ('cells', 2, 'outputs'):
        assert len(diff) == 1
        assert diff[0]['key'] == key
        assert diff[0]['op'] == 'patch'
        diff = diff[0]['diff']


def test_nbdiff_app_only_details(filespath, tmpdir, reset_notebook_diff):
    afn = os.path.join(filespath, "single_cell_nb.ipynb")
    bfn = os.path.join(filespath, "single_cell_nb--changed_source_output_ec.ipynb")
    dfn = os.path.join(tmpdir.dirname, "diff_output.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--out', dfn, '-d'])
    assert 0 == main_diff(args)
    with io.open(dfn) as df:
        diff = json.load(df)
    print(diff)
    for key in ('cells', 0):
        assert len(diff) == 1
        assert diff[0]['key'] == key
        assert diff[0]['op'] == 'patch'
        diff = diff[0]['diff']
    assert len(diff) == 1
    assert diff[0]['key'] == 'execution_count'
    assert diff[0]['op'] == 'replace'
    assert diff[0]['value'] == 2


def test_nbdiff_app_ignore_details(filespath, tmpdir, reset_notebook_diff):
    afn = os.path.join(filespath, "single_cell_nb.ipynb")
    bfn = os.path.join(filespath, "single_cell_nb--changed_source_output_ec.ipynb")
    dfn = os.path.join(tmpdir.dirname, "diff_output.json")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--out', dfn, '-D'])
    assert 0 == main_diff(args)
    with io.open(dfn) as df:
        diff = json.load(df)
    print(diff)
    for key in ('cells', 0):
        assert len(diff) == 1
        assert diff[0]['key'] == key
        assert diff[0]['op'] == 'patch'
        diff = diff[0]['diff']
    assert len(diff) == 2
    assert diff[0]['key'] == 'outputs'
    for subdiff in diff[0]['diff']:
        assert subdiff['op'] != 'patch'

    assert diff[1]['key'] == 'source'


def test_nbdiff_app_config_ignores(filespath, tmpdir, reset_notebook_diff):
    tmpdir.join('nbdime_config.json').write_text(
        json.dumps({
            'Diff': {
                'Ignore': {
                    '/cells/*/metadata': ['nbdime-dummy-field']
                }
            },
        }),
        encoding='utf-8'
    )

    afn = os.path.join(filespath, "single_cell_nb.ipynb")
    bfn = os.path.join(filespath, "single_cell_nb--changed_metadata.ipynb")
    dfn = os.path.join(tmpdir.dirname, "diff_output.json")
    with tmpdir.as_cwd():
        args = nbdiffapp._build_arg_parser('nbdiff').parse_args([afn, bfn, '--out', dfn])
    assert 0 == main_diff(args)

    pprint(notebook_differs)

    with io.open(dfn) as df:
        diff = json.load(df)
    pprint(diff)
    for key in ('metadata', 'language_info'):
        assert len(diff) == 1
        assert diff[0]['key'] == key
        assert diff[0]['op'] == 'patch'
        diff = diff[0]['diff']

    assert len(diff) == 1
    assert diff[0]['key'] == 'version'
    assert diff[0]['op'] == 'patch'


def test_nbdiff_app_flags_override_config_ignores(filespath, tmpdir, reset_notebook_diff):
    # This excercises current behavior, but should ideally (?) be different

    tmpdir.join('nbdime_config.json').write_text(
        json.dumps({
            'Diff': {
                'Ignore': {
                    '/cells/*/metadata': ['nbdime-dummy-field']
                }
            },
        }),
        encoding='utf-8'
    )

    afn = os.path.join(filespath, "single_cell_nb.ipynb")
    bfn = os.path.join(filespath, "single_cell_nb--changed_metadata.ipynb")
    dfn = os.path.join(tmpdir.dirname, "diff_output.json")
    with tmpdir.as_cwd():
        args = nbdiffapp._build_arg_parser('nbdiff').parse_args([afn, bfn, '--out', dfn, '-S'])
    assert 0 == main_diff(args)

    pprint(notebook_differs)

    with io.open(dfn) as df:
        diff = json.load(df)
    pprint(diff)

    assert len(diff) == 2
    assert diff[0]['key'] == 'cells'
    assert diff[1]['key'] == 'metadata'


def test_nbdiff_app_color_words(filespath):
    # Simply check that the --color-words argument is accepted, not behavior
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--color-words'])
    assert 0 == main_diff(args)


def test_nbdiff_app_no_colors(filespath, capsys):
    # Simply check that the --color-words argument is accepted, not behavior
    # Behavior is covered elsewhere
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    args = nbdiffapp._build_arg_parser().parse_args([afn, bfn, '--no-color'])
    assert 0 == main_diff(args)


def test_nbmerge_app(tempfiles, capsys, reset_log):
    bfn = os.path.join(tempfiles, "multilevel-test-base.ipynb")
    lfn = os.path.join(tempfiles, "multilevel-test-local.ipynb")
    rfn = os.path.join(tempfiles, "multilevel-test-remote.ipynb")
    ofn = os.path.join(tempfiles, "output.ipynb")

    args = nbmergeapp._build_arg_parser().parse_args([bfn, lfn, rfn, '--log-level=DEBUG'])
    assert args.log_level == 'DEBUG'
    assert nbdime.log.logger.level == logging.DEBUG

    assert 0 == main_merge(args)

    nb_stdout, err = capsys.readouterr()

    assert 0 == nbmergeapp.main([bfn, lfn, rfn, '--out', ofn])
    out, err = capsys.readouterr()
    # no stdout when sending output to file
    assert out == ''

    assert os.path.exists(ofn)

    with io.open(ofn, 'r', encoding='utf8') as f:
        nb_file = f.read()

    assert nb_stdout == nb_file


def test_nbmerge_app_null_base(filespath, reset_log):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    # Two identical files added (null base)
    args = nbmergeapp._build_arg_parser().parse_args([
        EXPLICIT_MISSING_FILE, afn, afn])
    assert 0 == main_merge(args)

    # Two conflicting files added (null base)
    args = nbmergeapp._build_arg_parser().parse_args([
        EXPLICIT_MISSING_FILE, afn, bfn])
    assert 1 == main_merge(args)


def test_nbmerge_app_null_side(filespath, reset_log):
    afn = os.path.join(filespath, "multilevel-test-base.ipynb")
    bfn = os.path.join(filespath, "multilevel-test-local.ipynb")

    # Local deleted, remote modified
    args = nbmergeapp._build_arg_parser().parse_args([
        afn, EXPLICIT_MISSING_FILE, bfn])
    assert 1 == main_merge(args)

    # Remote deleted, local modified
    args = nbmergeapp._build_arg_parser().parse_args([
        afn, bfn, EXPLICIT_MISSING_FILE])
    assert 1 == main_merge(args)

    # Both deleted
    args = nbmergeapp._build_arg_parser().parse_args([
        afn, EXPLICIT_MISSING_FILE, EXPLICIT_MISSING_FILE])
    assert 0 == main_merge(args)


def test_nbmerge_app_conflict(tempfiles, capsys, reset_log):
    bfn = os.path.join(tempfiles, "inline-conflict--1.ipynb")
    lfn = os.path.join(tempfiles, "inline-conflict--2.ipynb")
    rfn = os.path.join(tempfiles, "inline-conflict--3.ipynb")
    ofn = os.path.join(tempfiles, "inline-conflict-out.ipynb")

    assert 1 == nbmergeapp.main([bfn, lfn, rfn])
    nb_stdout, err = capsys.readouterr()

    assert 1 == nbmergeapp.main([bfn, lfn, rfn, '--out', ofn])
    out, err = capsys.readouterr()
    # no stdout when sending output to file
    assert out == ''

    assert os.path.exists(ofn)

    with io.open(ofn, 'r', encoding='utf8') as f:
        nb_file = f.read()

    assert nb_stdout == nb_file


def test_nbmerge_app_decisions(tempfiles, capsys, caplog, reset_log):
    bfn = os.path.join(tempfiles, "inline-conflict--1.ipynb")
    lfn = os.path.join(tempfiles, "inline-conflict--2.ipynb")
    rfn = os.path.join(tempfiles, "inline-conflict--3.ipynb")

    assert 1 == nbmergeapp.main([bfn, lfn, rfn, '--decisions'])

    # ensure decisions are logged with warning:
    assert len(caplog.records) == 2
    assert caplog.records[0].levelno == logging.WARNING
    assert caplog.records[1].levelno == logging.WARNING
    assert 'conflicted decisions' in caplog.text

    # Assert no other stderr
    out = capsys.readouterr()[0]
    assert out == ''


def test_nbmerge_app_decisions_outfile(tempfiles, capsys, caplog, reset_log):
    bfn = os.path.join(tempfiles, "inline-conflict--1.ipynb")
    lfn = os.path.join(tempfiles, "inline-conflict--2.ipynb")
    rfn = os.path.join(tempfiles, "inline-conflict--3.ipynb")
    ofn = os.path.join(tempfiles, "inline-conflict-out.ipynb")

    assert 1 == nbmergeapp.main([bfn, lfn, rfn, '--decisions', '--out', ofn])

    # ensure decisions are logged with warning:
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert 'Conflicts occurred during merge operation' in caplog.text

    # Assert no other stderr
    out = capsys.readouterr()[0]
    assert out == ''

    # Write decisions to output file as JSON if requested
    with open(os.path.join(tempfiles, 'inline-conflict--decisions.json')) as f:
        expected = f.read()
    with open(ofn) as f:
        actual = f.read()
    assert expected == actual


def test_nbmerge_app_no_colors(filespath):
    # Simply check that the --color-words argument is accepted, not behavior
    bfn = os.path.join(filespath, "multilevel-test-base.ipynb")
    lfn = os.path.join(filespath, "multilevel-test-local.ipynb")
    rfn = os.path.join(filespath, "multilevel-test-remote.ipynb")

    args = nbmergeapp._build_arg_parser().parse_args([bfn, lfn, rfn, '--no-color'])
    assert 0 == main_merge(args)


def test_diffdriver_config(git_repo):
    main = gitdiffdriver.main
    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    _check_diffdriver_enabled()

    main(['config', '--disable'])
    _check_diffdriver_disabled()


def _check_diffdriver_enabled():
    assert os.path.exists('.gitattributes')
    with io.open('.gitattributes', 'r', encoding='utf8') as f:
        gitattributes = f.read()
    assert 'jupyternotebook' in gitattributes
    out = get_output('git config --get --local diff.jupyternotebook.command')
    assert 'git-nbdiffdriver' in out


def _check_diffdriver_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local diff.jupyternotebook.command')


def test_difftool_config(git_repo):
    main = gitdifftool.main

    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    _check_difftool_enabled()

    main(['config', '--enable', '--set-default'])
    out = get_output('git config --get --local diff.guitool')
    assert 'nbdime' == out.strip()

    main(['config', '--disable'])
    _check_difftool_disabled()


def _check_difftool_enabled():
    out = get_output('git config --get --local difftool.nbdime.cmd')
    assert 'git-nbdifftool' in out

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local diff.guitool')


def _check_difftool_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local diff.guitool')


def test_mergedriver_config(git_repo):
    main = gitmergedriver.main
    with assert_clean_exit():
        main(['config', '-h'])
    assert not os.path.exists('.gitattributes')

    main(['config', '--enable'])
    _check_mergedriver_enabled()

    main(['config', '--disable'])
    _check_mergedriver_disabled()


def _check_mergedriver_enabled():
    assert os.path.exists('.gitattributes')
    with io.open('.gitattributes', 'r', encoding='utf8') as f:
        gitattributes = f.read()
    assert 'jupyternotebook' in gitattributes
    out = get_output('git config --get --local merge.jupyternotebook.driver')
    assert 'git-nbmergedriver' in out


def _check_mergedriver_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local merge.jupyternotebook.driver')


def test_mergetool_config(git_repo):
    main = gitmergetool.main
    with assert_clean_exit():
        main(['config', '-h'])

    main(['config', '--enable'])
    _check_mergetool_enabled()

    main(['config', '--enable', '--set-default'])
    out = get_output('git config --get --local merge.tool')
    assert 'nbdime' == out.strip()

    main(['config', '--disable'])
    _check_mergetool_disabled()


def _check_mergetool_enabled():
    out = get_output('git config --get --local mergetool.nbdime.cmd')
    assert 'git-nbmergetool' in out

    with pytest.raises(CalledProcessError):
        out = get_output('git config --get --local merge.tool')


def _check_mergetool_disabled():
    with pytest.raises(CalledProcessError):
        get_output('git config --get --local merge.tool')


def test_config_git(git_repo):
    """Check that `nbime config-git` command works"""

    main_dispatch(['config-git', '--enable'])

    _check_diffdriver_enabled()
    _check_difftool_enabled()
    _check_mergedriver_enabled()
    _check_mergetool_enabled()

    main_dispatch(['config-git', '--disable'])

    _check_diffdriver_disabled()
    _check_difftool_disabled()
    _check_mergedriver_disabled()
    _check_mergetool_disabled()


def test_config_git_fails(git_repo):
    """Check that `nbime config-git` command fails given invalid option"""
    # Check that it either gives non-zero return code (or exit code)
    try:
        code = main_dispatch(['config-git', '--foo'])
        assert code != 0
    except SystemExit as e:
        assert e.code != 0
    finally:
        _check_diffdriver_disabled()
        _check_difftool_disabled()
        _check_mergedriver_disabled()
        _check_mergetool_disabled()


def test_git_diffdriver(git_repo):
    gitdiffdriver.main(['config', '--enable'])
    out = get_output('git diff base diff.ipynb')
    assert 'nbdiff' in out


def test_git_mergedriver(git_repo, filespath):
    # enable diff/merge drivers
    gitdiffdriver.main(['config', '--enable'])
    gitmergedriver.main(['config', '--enable'])
    # run merge with no conflicts
    out = get_output('git merge remote-no-conflict', err=True)
    assert 'Auto-merging merge-no-conflict.ipynb' in out
    with open('merge-no-conflict.ipynb') as f:
        merged = f.read()

    with open(os.path.join(filespath, 'multilevel-test-merged.ipynb')) as f:
        expected = f.read()

    # verify merge success
    assert merged == expected

    # reset
    call('git reset local --hard')

    # run merge with conflicts
    with pytest.raises(CalledProcessError):
        call('git merge remote-conflict')

    status = get_output('git status')
    assert 'merge-conflict.ipynb' in status
    out = get_output('git diff HEAD')
    assert 'nbdiff' in out
    # verify that the conflicted result is a valid notebook
    nb = nbformat.read('merge-conflict.ipynb', as_version=4)
    nbformat.validate(nb)


@pytest.mark.timeout(timeout=3*WEB_TEST_TIMEOUT)
def test_git_difftool(git_repo, unique_port, popen_with_terminator):
    gitdifftool.main(['config', '--enable'])
    cmd = get_output('git config --get --local difftool.nbdime.cmd').strip()

    # pick a non-random port so we can connect later, and avoid opening a browser
    port = unique_port
    cmd = cmd + ' --port=%i --browser=disabled' % port
    call(['git', 'config', 'difftool.nbdime.cmd', cmd])

    # avoid global diff driver config from disabling difftool:
    with open('.gitattributes', 'w') as f:
        f.write('*.ipynb\tdiff=notnbdime')

    process = popen_with_terminator(['git', 'difftool', '--tool=nbdime', 'base'])

    # 3 is the number of notebooks in this diff
    url = 'http://127.0.0.1:%i' % port
    for _ in range(3):
        wait_up(url, check=lambda: process.poll() is None)
        # server started
        s = requests.Session()
        r = s.get(url + '/difftool')
        r.raise_for_status()
        # close it
        r = s.post(url + '/api/closetool', data={
            'exitCode': 0,
            '_xsrf': r.cookies['_xsrf']
        })
        r.raise_for_status()
        time.sleep(0.25)
    # wait for exit
    process.wait()
    assert process.poll() == 0


@pytest.mark.timeout(timeout=3*WEB_TEST_TIMEOUT)
def test_git_mergetool(git_repo, unique_port, popen_with_terminator):
    gitmergetool.main(['config', '--enable'])
    cmd = get_output('git config --get --local mergetool.nbdime.cmd').strip()

    # pick a non-random port so we can connect later, and avoid opening a browser
    port = unique_port
    cmd = cmd + ' --port=%i --browser=disabled' % port
    call(['git', 'config', 'mergetool.nbdime.cmd', cmd])
    call(['git', 'config', 'mergetool.nbdime.trustExitCode', 'true'])

    with pytest.raises(CalledProcessError):
        call('git merge remote-conflict')
    process = popen_with_terminator([
        'git', 'mergetool', '--no-prompt', '--tool=nbdime', 'merge-conflict.ipynb'])

    # 3 total web calls: mergetool, api/store, api/closetool
    url = 'http://127.0.0.1:%i' % port
    wait_up(url, check=lambda: process.poll() is None)
    # server started
    s = requests.Session()
    r = s.get(url + '/mergetool')
    r.raise_for_status()
    xsrf = r.cookies['_xsrf']
    r = s.post(
        url_concat(url + '/api/store', {'outputfilename': 'merge-conflict.ipynb'}),
        json={'merged': nbformat.v4.new_notebook()},
        headers={'X-XSRFToken': xsrf},
    )
    r.raise_for_status()
    # close it
    r = s.post(
        url + '/api/closetool',
        data={
            'exitCode': 0,
            '_xsrf': xsrf,
        }
    )
    r.raise_for_status()
    # wait for exit
    process.wait()
    assert process.poll() == 0


def test_hg_diff(hg_repo):
    write_local_hg_config(hg_repo)
    # ExtDiff for some reason always returns 1.
    out = get_output('hg nbdiff -r base:local diff.ipynb', returncode=1)
    assert 'nbdiff' in out


def test_hg_mergedriver(hg_repo, filespath, reset_log):
    # enable diff/merge drivers
    write_local_hg_config(hg_repo)
    # run merge with no conflicts
    out = get_output('hg merge remote-no-conflict', err=True)
    assert 'nbmergeapp' in out
    with open('merge-no-conflict.ipynb') as f:
        merged = f.read()

    with open(os.path.join(filespath, 'multilevel-test-merged.ipynb')) as f:
        expected = f.read()

    # verify merge success
    assert merged == expected

    # reset
    call('hg update --clean local')

    # run merge with conflicts
    with pytest.raises(CalledProcessError):
        call('hg merge remote-conflict')

    status = get_output('hg status')
    assert 'merge-conflict.ipynb' in status
    out = get_output('hg nbdiff', returncode=1)
    assert 'nbdiff' in out
    # verify that the conflicted result is a valid notebook
    nb = nbformat.read('merge-conflict.ipynb', as_version=4)
    nbformat.validate(nb)



@pytest.mark.timeout(timeout=3*WEB_TEST_TIMEOUT)
def test_hg_diffweb(hg_repo, unique_port, popen_with_terminator):
    # enable diff/merge drivers
    write_local_hg_config(hg_repo)

    process = popen_with_terminator([
        'hg', 'nbdiffweb', '-r', 'base', '-o', '--port=%i' % unique_port])

    # 3 is the number of notebooks in this diff
    url = 'http://127.0.0.1:%i' % unique_port
    wait_up(url, check=lambda: process.poll() is None)
    for _ in range(3):
        # server started
        s = requests.Session()
        r = s.get(url + '/difftool')
        r.raise_for_status()
        # close it
        r = s.post(url + '/api/closetool', data={
            'exitCode': 0,
            '_xsrf': r.cookies['_xsrf']
        })
        r.raise_for_status()
        time.sleep(0.25)
    # wait for exit
    process.wait()
    assert process.poll() == 1  # hg ExtDiff returns 1 for some reason


@pytest.mark.timeout(timeout=WEB_TEST_TIMEOUT)
def test_hg_mergetool(hg_repo, unique_port, popen_with_terminator):
    # enable diff/merge drivers
    write_local_hg_config(hg_repo)

    with pytest.raises(CalledProcessError):
        call('hg merge remote-conflict')
    config_override = '--log-level DEBUG --browser=disabled --port=%d $base $local $other $output' % unique_port
    process = popen_with_terminator([
        'hg', 'resolve', '--tool', 'nbdimeweb',
        '--config', 'merge-tools.nbdimeweb.args=%s' % config_override,
        'merge-conflict.ipynb'])

    url = 'http://127.0.0.1:%i' % unique_port
    wait_up(url, check=lambda: process.poll() is None)
    # server started
    s = requests.Session()
    r = s.get(url + '/mergetool')
    r.raise_for_status()
    xsrf = r.cookies['_xsrf']
    r = s.post(
        url_concat(url + '/api/store', {'outputfilename': 'merge-conflict.ipynb'}),
        json={'merged': nbformat.v4.new_notebook()},
        headers={'X-XSRFToken': xsrf},
    )
    r.raise_for_status()
    # close it
    r = s.post(
        url + '/api/closetool',
        data={
            'exitCode': 0,
            '_xsrf': xsrf
        }
    )
    r.raise_for_status()
    # wait for exit
    process.wait()
    assert process.poll() == 0
