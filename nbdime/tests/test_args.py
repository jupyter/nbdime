
import argparse
import pytest
import json

from traitlets import Enum

from nbdime.args import (
    SkipAction, ConfigBackedParser, LogLevelAction,
)
from nbdime.config import (
    entrypoint_configurables, Global, _Ignorables
)
import nbdime.diffing.notebooks
from nbdime.diffing.notebooks import notebook_differs, diff


class FixtureConfig(Global):
    log_level = Enum(
        ('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        'WARN',
    ).tag(config=True)

@pytest.fixture
def entrypoint_config():
    entrypoint_configurables['test-prog'] = FixtureConfig
    yield
    del entrypoint_configurables['test-prog']

class IgnorableConfig1(_Ignorables):
    pass

class IgnorableConfig2(IgnorableConfig1):
    pass

@pytest.fixture
def entrypoint_ignore_config():
    entrypoint_configurables['test-prog'] = IgnorableConfig2
    yield
    del entrypoint_configurables['test-prog']


def test_skip_action():
    parser = argparse.ArgumentParser()
    parser.add_argument('a')
    parser.add_argument('b', action=SkipAction)

    opts = parser.parse_args(['fileA', 'fileB'])

    assert opts.a == 'fileA'
    assert not hasattr(opts, 'b')


def test_config_parser(entrypoint_config):
    parser = ConfigBackedParser('test-prog')
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        help="Set the log level by name.",
        action=LogLevelAction,
    )

    # Check that log level default is taken from FixtureConfig
    arguments = parser.parse_args([])
    assert arguments.log_level == 'WARN'

    arguments = parser.parse_args(['--log-level', 'ERROR'])
    assert arguments.log_level == 'ERROR'


def test_ignore_config_simple(entrypoint_ignore_config, tmpdir, reset_notebook_diff):
    tmpdir.join('nbdime_config.json').write_text(
        json.dumps({
            'IgnorableConfig1': {
                'Ignore': {
                    '/cells/*/metadata': ['collapsed', 'autoscroll']
                }
            },
        }),
        encoding='utf-8'
    )

    def mock_ignore_keys(inner, keys):
        return (inner, keys)
    parser = ConfigBackedParser('test-prog')
    old_keys = nbdime.diffing.notebooks.diff_ignore_keys
    nbdime.diffing.notebooks.diff_ignore_keys = mock_ignore_keys
    try:
        with tmpdir.as_cwd():
            parser.parse_args([])
    finally:
        nbdime.diffing.notebooks.diff_ignore_keys = old_keys

    assert notebook_differs['/cells/*/metadata'] == (diff, ['collapsed', 'autoscroll'])



def test_ignore_config_merge(entrypoint_ignore_config, tmpdir, reset_notebook_diff):
    tmpdir.join('nbdime_config.json').write_text(
        json.dumps({
            'IgnorableConfig1': {
                'Ignore': {
                    '/cells/*/metadata': ['collapsed', 'autoscroll']
                }
            },
            'IgnorableConfig2': {
                'Ignore': {
                    '/metadata': ['foo'],
                    '/cells/*/metadata': ['tags']
                }
            },
        }),
        encoding='utf-8'
    )

    def mock_ignore_keys(inner, keys):
        return (inner, keys)
    parser = ConfigBackedParser('test-prog')
    old_keys = nbdime.diffing.notebooks.diff_ignore_keys
    nbdime.diffing.notebooks.diff_ignore_keys = mock_ignore_keys
    try:
        with tmpdir.as_cwd():
            parser.parse_args([])
    finally:
        nbdime.diffing.notebooks.diff_ignore_keys = old_keys

    assert notebook_differs['/metadata'] == (diff, ['foo'])
    # Lists are not merged:
    assert notebook_differs['/cells/*/metadata'] == (diff, ['tags'])


def test_config_inherit(entrypoint_ignore_config, tmpdir, reset_notebook_diff):
    tmpdir.join('nbdime_config.json').write_text(
        json.dumps({
            'IgnorableConfig1': {
                'metadata': False
            },
        }),
        encoding='utf-8'
    )

    parser = ConfigBackedParser('test-prog')
    with tmpdir.as_cwd():
        parsed = parser.parse_args([])

    assert parsed.metadata is False
