
import argparse
import pytest

from traitlets import Enum

from nbdime.args import (
    SkipAction, ConfigBackedParser, LogLevelAction,
)
from nbdime.config import entrypoint_configurables, Global


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
