import freezegun
from requests import Session
from requests_mock import GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ESKOM import fetch_production, get_url


@freezegun.freeze_time("2023-09-22")
def test_production(snapshot):
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)
    with open("parsers/test/mocks/ESKOM/Station_Build_Up.csv", "rb") as mock_file:
        adapter.register_uri(
            GET,
            get_url(),
            content=mock_file.read(),
        )

    production = fetch_production(
        zone_key=ZoneKey("ZA"),
        session=session,
    )
    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "production": element["production"],
                "storage": element["storage"],
                "source": element["source"],
                "zoneKey": element["zoneKey"],
                "sourceType": element["sourceType"].value,
            }
            for element in production
        ]
    )
