import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--datadir", action="store", default=None, help="Path to directory containing data for tests"
    )


@pytest.fixture()
def root_data_dir(request):
    """Path to directory containing data for tests"""
    return request.config.getoption("--datadir")
