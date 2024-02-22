from datetime import datetime, timezone

import pytest
from requests import Session
from requests_mock import GET, POST, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.IEMOP import REPORTS_ADMIN_URL, fetch_production

zone_keys = [ZoneKey("PH-LU"), ZoneKey("PH-MI"), ZoneKey("PH-VI")]


@pytest.mark.parametrize("zone_key", zone_keys)
def test_production(snapshot, zone_key: ZoneKey):
    """
    Reports have been reduced to 14 September 2023 00:00 to 13 September 2023 22:00 for ease
    """
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)
    target_datetime = datetime(2023, 9, 14, 0, 0, tzinfo=timezone.utc)
    with open(
        "parsers/test/mocks/IEMOP/list_reports_items.json", "rb"
    ) as list_reports_items:
        adapter.register_uri(
            POST,
            REPORTS_ADMIN_URL,
            content=list_reports_items.read(),
        )
    REPORTS_LINK = "https://www.iemop.ph/market-data/dipc-energy-results-raw/?md_file=L3Zhci93d3cvaHRtbC93cC1jb250ZW50L3VwbG9hZHMvZG93bmxvYWRzL2RhdGEvRElQQ0VSL0RJUENFUl8yMDIzMDkxNDAwMDAuemlw"
    with open("parsers/test/mocks/IEMOP/reports_content", "rb") as reports_byte_content:
        adapter.register_uri(
            GET,
            REPORTS_LINK,
            content=reports_byte_content.read(),
        )
    production = fetch_production(
        zone_key=ZoneKey(zone_key),
        session=session,
        target_datetime=target_datetime,
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
