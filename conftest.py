import pytest

def pytest_addoption(parser):
    parser.addoption("--quick", action="store_true",
                     default=False, help="skip slow tests")
    parser.addoption("--slow", action="store_true",
                     default=False, help="only run slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--slow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_quick = pytest.mark.skip(reason="skipping all tests that are not slow")
    for item in items:
        if 'slow' not in item.fixturenames:
            item.add_marker(skip_quick)
