import pytest
import requests
import requests_mock


@pytest.fixture()
def fixture_session_mock() -> tuple[requests.Session, requests_mock.Adapter]:
    session = requests.Session()

    adapter = requests_mock.Adapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session, adapter
