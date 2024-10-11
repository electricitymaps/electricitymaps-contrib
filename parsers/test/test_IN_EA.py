from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from requests import Session
from requests_mock import GET, Adapter

from electricitymap.contrib.config import ZONE_NEIGHBOURS, ZoneKey
from parsers import IN_EA

NETFLOWS = {
    ZoneKey("IN-EA->IN-NO"): -2139.0,
    ZoneKey("IN-EA->IN-NE"): -1518.0,
    ZoneKey("IN-EA->IN-SO"): -3019.0,
    ZoneKey("IN-EA->IN-WE"): 3257.0,
    ZoneKey("BT->IN-EA"): 769.75,
    ZoneKey("IN-EA->NP"): 274.17,
    ZoneKey("BD->IN-EA"): -936.79,
}


@pytest.mark.parametrize("neighbour_zone_key", ZONE_NEIGHBOURS[ZoneKey("IN-EA")])
def test_exchanges(neighbour_zone_key: ZoneKey):
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)
    target_date = datetime(2023, 6, 25, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    sorted_zone_keys = ZoneKey("->".join(sorted([neighbour_zone_key, "IN-EA"])))
    url, _ = IN_EA.get_fetch_function(sorted_zone_keys)
    filename = (
        "interregional_exchanges"
        if sorted_zone_keys in IN_EA.INTERREGIONAL_EXCHANGES
        else "transnational_exchanges"
    )
    with open(f"parsers/test/mocks/IN_EA/{filename}.json", "rb") as data:
        adapter.register_uri(
            GET,
            url.format(
                proxy=IN_EA.IN_WE_PROXY,
                host=IN_EA.HOST,
                target_date=target_date.strftime("%Y-%m-%d"),
            ),
            content=data.read(),
        )
    exchanges = IN_EA.fetch_exchange(
        ZoneKey("IN-EA"),
        neighbour_zone_key,
        session,
        datetime(2023, 6, 25, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
    )

    assert exchanges[0]["datetime"] == datetime(
        2023, 6, 25, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata")
    )
    assert exchanges[0]["netFlow"] == NETFLOWS[sorted_zone_keys]
    assert exchanges[0]["sortedZoneKeys"] == sorted_zone_keys
