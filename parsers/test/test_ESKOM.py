import freezegun
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ESKOM import fetch_production, get_url


@freezegun.freeze_time("2023-09-22")
def test_production(adapter, session, snapshot):
    with open("parsers/test/mocks/ESKOM/Station_Build_Up.csv", "rb") as mock_file:
        adapter.register_uri(
            GET,
            get_url(),
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(zone_key=ZoneKey("ZA"), session=session)
