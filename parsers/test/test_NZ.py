from importlib import resources
from json import loads

from requests_mock import GET

from parsers.NZ import PRICE_URL, PRODUCTION_URL, fetch_price, fetch_production


def test_snapshot_production_data(adapter, session, snapshot):
    with open(
        resources.files("parsers.test.mocks.NZ").joinpath(
            "response_2024_04_24_17_30.html"
        )
    ) as f:
        adapter.register_uri(
            GET,
            PRODUCTION_URL,
            text=f.read(),
        )
    with open(
        resources.files("parsers.test.mocks.NZ").joinpath(
            "response_2024_04_24_18_00.html"
        )
    ) as f:
        adapter.register_uri(
            GET,
            PRODUCTION_URL,
            text=f.read(),
        )

    production = []
    production.append(fetch_production(zone_key="NZ", session=session))
    production.append(fetch_production(zone_key="NZ", session=session))

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "production": element["production"],
            "storage": element["storage"],
            "capacity": element["capacity"],
            "source": element["source"],
        }
        for element in production
    ]


def test_snapshot_price_data(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        PRICE_URL,
        json=loads(
            resources.files("parsers.test.mocks.NZ")
            .joinpath("response_2024_04_24_18_00.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        PRICE_URL,
        json=loads(
            resources.files("parsers.test.mocks.NZ")
            .joinpath("response_2024_04_24_18_30.json")
            .read_text()
        ),
    )

    price = []
    price.append(fetch_price(zone_key="NZ", session=session))
    price.append(fetch_price(zone_key="NZ", session=session))

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "source": element["source"],
            "price": element["price"],
            "currency": element["currency"],
        }
        for element in price
    ]
