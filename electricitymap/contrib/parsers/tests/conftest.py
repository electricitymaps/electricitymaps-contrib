"""
Pytest fixtures for parser tests.

`session` is a plain `requests.Session` — production-equivalent. To
intercept HTTP calls, tests use the `requests_mock` pytest fixture
(auto-provided by `requests-mock`), which monkey-patches
`Session.get_adapter` transparently. This means production code is free
to mount HTTPAdapter / Retry / any other transport adapter on
`session.adapters` without interfering with test interception — handy
for parsers that want retry-on-429 behaviour.

Fixtures ref: https://docs.pytest.org/en/stable/explanation/fixtures.html
requests-mock ref: https://requests-mock.readthedocs.io/en/latest/pytest.html
"""

import pytest
from requests import Session


@pytest.fixture
def session():
    yield Session()
