from pathlib import Path

from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENERCAL

base_path_to_mock = Path("parsers/test/mocks/ENERCAL")


def test_production_with_snapshot(adapter, session, snapshot):
    raw_data = Path(base_path_to_mock, "production.json")
    adapter.register_uri(
        GET,
        ANY,
        content=raw_data.read_bytes(),
    )
    production = ENERCAL.fetch_production(ZoneKey("NC"), session)

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "correctedModes": element["correctedModes"],
        }
        for element in production
    ]
