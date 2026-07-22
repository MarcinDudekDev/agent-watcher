"""`live` tests call the model: slow, non-deterministic, and skipped by default.

    uv run --with pytest pytest watcher/            # offline only
    uv run --with pytest pytest watcher/ --live     # includes the model calls
"""


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", default=False,
                     help="run the tests that call the supervisor model")


def pytest_configure(config):
    config.addinivalue_line("markers", "live: calls the model")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live"):
        return
    import pytest
    skip = pytest.mark.skip(reason="needs --live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
