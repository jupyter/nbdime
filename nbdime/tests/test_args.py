
import argparse

from nbdime.args import SkipAction


def test_skip_action():
    parser = argparse.ArgumentParser()
    parser.add_argument('a')
    parser.add_argument('b', action=SkipAction)

    opts = parser.parse_args(['fileA', 'fileB'])

    assert opts.a == 'fileA'
    assert not hasattr(opts, 'b')
