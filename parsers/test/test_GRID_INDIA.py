from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from requests_mock import GET

from electricitymap.contrib.config import ZONE_NEIGHBOURS, ZoneKey
from parsers import GRID_INDIA


@pytest.mark.parametrize("neighbour_zone_key", ZONE_NEIGHBOURS[ZoneKey("IN-EA")])
def test_exchanges(adapter, session, snapshot, neighbour_zone_key: ZoneKey):
    target_date = datetime(2023, 6, 25, tzinfo=ZoneInfo("Asia/Kolkata"))

    pdfurl = GRID_INDIA.get_psp_report_file_url(target_date)

    with open("test/mocks/GRID_INDIA/exchanges.pdf", "rb") as data:
        adapter.register_uri(
            GET,
            pdfurl,
            content=data.read(),
        )
    assert snapshot == GRID_INDIA.fetch_exchange(
        ZoneKey("IN-EA"),
        neighbour_zone_key,
        session,
        datetime(2023, 6, 25, tzinfo=ZoneInfo("Asia/Kolkata")),
    )
