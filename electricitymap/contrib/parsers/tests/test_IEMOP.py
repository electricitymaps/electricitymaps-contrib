from datetime import datetime, timezone

import pytest
from requests_mock import GET, POST

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.IEMOP import REPORTS_ADMIN_URL, fetch_production

zone_keys = [ZoneKey("PH-LU"), ZoneKey("PH-MI"), ZoneKey("PH-VI")]


@pytest.mark.parametrize("zone_key", zone_keys)
def test_production(adapter, session, snapshot, zone_key: ZoneKey):
    """
    Reports have been reduced to 14 September 2023 00:00 to 13 September 2023 22:00 for ease
    """
    target_datetime = datetime(2023, 9, 14, 0, 0, tzinfo=timezone.utc)
    with open(
        "electricitymap/contrib/parsers/tests/mocks/IEMOP/list_reports_items.json", "rb"
    ) as list_reports_items:
        adapter.register_uri(
            POST,
            REPORTS_ADMIN_URL,
            content=list_reports_items.read(),
        )
    REPORTS_LINK = "https://www.iemop.ph/market-data/dipc-energy-results-raw/?md_file=L3Zhci93d3cvaHRtbC93cC1jb250ZW50L3VwbG9hZHMvZG93bmxvYWRzL2RhdGEvRElQQ0VSL0RJUENFUl8yMDIzMDkxNDAwMDAuemlw"
    with open(
        "electricitymap/contrib/parsers/tests/mocks/IEMOP/reports_content", "rb"
    ) as reports_byte_content:
        adapter.register_uri(
            GET,
            REPORTS_LINK,
            content=reports_byte_content.read(),
        )
    assert snapshot == fetch_production(
        zone_key=ZoneKey(zone_key),
        session=session,
        target_datetime=target_datetime,
    )
