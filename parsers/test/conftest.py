import pytest
from requests import Session
from requests_mock import Adapter


@pytest.fixture
def adapter():
    adapter = Adapter()
    yield adapter


@pytest.fixture
def session(adapter):
    session = Session()
    session.mount("https://", adapter)
    yield session
