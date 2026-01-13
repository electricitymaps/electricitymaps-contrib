import freezegun
from requests_mock import GET

from electricitymap.contrib.parsers.ESKOM import fetch_production, get_url
from electricitymap.types import ZoneKey


@freezegun.freeze_time("2023-09-22")
def test_production(adapter, session, snapshot):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/ESKOM/Station_Build_Up.csv", "rb"
    ) as mock_file:
        adapter.register_uri(
            GET,
            get_url(),
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(zone_key=ZoneKey("ZA"), session=session)
