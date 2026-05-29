import json
from importlib import resources

from requests_mock import ANY, GET

from electricitymap.contrib.parsers.CA_QC import fetch_consumption, fetch_production


def test_production(requests_mock, session, snapshot):
    requests_mock.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.Hydroquebec")
            .joinpath("production.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(session=session)


def test_consumption(requests_mock, session, snapshot):
    requests_mock.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.Hydroquebec")
            .joinpath("consumption.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_consumption(session=session)
