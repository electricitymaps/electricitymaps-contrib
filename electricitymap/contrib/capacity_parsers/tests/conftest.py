"""
This is a configuration file for pytest that defines test fixtures available for
use by all tests under this path.

Fixtures ref: https://docs.pytest.org/en/stable/explanation/fixtures.html
"""

import pytest
from requests import Session
from requests_mock import Adapter


@pytest.fixture
def adapter():
    """
    A `requests.Adapter` enables us to mock responses when making web requests
    via `requests.Session`.

    Adapter ref: https://requests.readthedocs.io/en/latest/user/advanced/#transport-adapters
    """
    adapter = Adapter()
    yield adapter


@pytest.fixture
def session(adapter):
    """
    A `request.Session` using the adapter fixture's object whenever http:// or
    https:// requests are made.

    Session ref: https://requests.readthedocs.io/en/latest/user/advanced/#session-objects
    """
    session = Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    yield session
