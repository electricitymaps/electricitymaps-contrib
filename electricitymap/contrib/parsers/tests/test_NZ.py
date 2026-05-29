from importlib import resources
from json import loads

from requests_mock import GET

from electricitymap.contrib.parsers.NZ import (
    PRICE_URL,
    PRODUCTION_URL,
    fetch_price,
    fetch_production,
)


def test_snapshot_production_data(requests_mock, session, snapshot):
    with open(
        resources.files("electricitymap.contrib.parsers.tests.mocks.NZ").joinpath(
            "response_2024_04_24_17_30.html"
        )
    ) as f:
        requests_mock.register_uri(
            GET,
            PRODUCTION_URL,
            text=f.read(),
        )
    with open(
        resources.files("electricitymap.contrib.parsers.tests.mocks.NZ").joinpath(
            "response_2024_04_24_18_00.html"
        )
    ) as f:
        requests_mock.register_uri(
            GET,
            PRODUCTION_URL,
            text=f.read(),
        )

    production = []
    production.append(fetch_production(zone_key="NZ", session=session))
    production.append(fetch_production(zone_key="NZ", session=session))

    assert snapshot == production


def test_snapshot_price_data(requests_mock, session, snapshot):
    requests_mock.register_uri(
        GET,
        PRICE_URL,
        json=loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.NZ")
            .joinpath("response_2024_04_24_18_00.json")
            .read_text()
        ),
    )
    requests_mock.register_uri(
        GET,
        PRICE_URL,
        json=loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.NZ")
            .joinpath("response_2024_04_24_18_30.json")
            .read_text()
        ),
    )

    price = []
    price.append(fetch_price(zone_key="NZ", session=session))
    price.append(fetch_price(zone_key="NZ", session=session))

    assert snapshot == price
