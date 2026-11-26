from datetime import UTC, datetime

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers import CSO
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

BANDS = [
    f"{h:02d}:{m:02d}  <  {h + (m + 30) // 60:02d}:{(m + 30) % 60:02d}"
    for h in range(24)
    for m in (0, 30)
] + ["All time periods"]
FUELS = ["Gas", "Wind", "Waste", "Pumped Storage Hydro", "Net Generation"]


def _meg01(days: dict[str, dict[tuple[int, str], float | None]]) -> dict:
    """A MEG01-shaped JSON-stat cube. ``days`` maps a day label to
    ``{(band_index, fuel): MWh}``; every other cell is null."""
    values = [
        cells.get((b, fuel))
        for cells in days.values()
        for b in range(len(BANDS))
        for fuel in FUELS
    ]
    labels = [["Metered Electricity Generation"], list(days), BANDS, FUELS]
    ids = ["STATISTIC", "TLIST(D1)", "C04199V04971", "C04200V04972"]
    return {
        "id": ids,
        "size": [len(x) for x in labels],
        "value": values,
        "dimension": {
            i: {"category": {"label": {str(k): v for k, v in enumerate(lab)}}}
            for i, lab in zip(ids, labels, strict=True)
        },
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    CSO._cache.clear()


def _fetch(requests_mock, session, days, start, end):
    requests_mock.register_uri(GET, CSO.MEG01_URL, json=_meg01(days))
    events = CSO.fetch_production_range(ZoneKey("IE"), session, start, end)
    return {e["datetime"]: e for e in events}


def test_mwh_per_half_hour_is_converted_to_mw_and_mapped(requests_mock, session):
    cells = {
        (24, "Gas"): 500.0,
        (24, "Wind"): 300.0,
        (24, "Waste"): 10.0,
        (24, "Pumped Storage Hydro"): 40.0,
        (24, "Net Generation"): 850.0,
    }
    events = _fetch(
        requests_mock,
        session,
        {"2021 June 01": cells},
        datetime(2021, 6, 1, tzinfo=UTC),
        datetime(2021, 6, 2, tzinfo=UTC),
    )
    # 2020-2022 bands are UTC: band 24 (12:00) is 12:00 UTC, even in summer.
    event = events[datetime(2021, 6, 1, 12, tzinfo=UTC)]
    assert event["production"] == {"gas": 1000.0, "wind": 600.0, "biomass": 20.0}
    assert event["storage"] == {"hydro": -80.0}
    assert event["source"] == "cso.ie"
    assert list(events) == [datetime(2021, 6, 1, 12, tzinfo=UTC)]


def test_spring_clock_change_bands_are_dropped_before_2023(requests_mock, session):
    # The DSO part is missing from 01:00-02:00 on spring clock-change days.
    cells = {(b, "Gas"): 100.0 for b in range(1, 5)}
    events = _fetch(
        requests_mock,
        session,
        {"2021 March 28": cells},
        datetime(2021, 3, 28, tzinfo=UTC),
        datetime(2021, 3, 29, tzinfo=UTC),
    )
    assert list(events) == [
        datetime(2021, 3, 28, 0, 30, tzinfo=UTC),
        datetime(2021, 3, 28, 2, 0, tzinfo=UTC),
    ]


def test_2023_bands_are_irish_local_time(requests_mock, session):
    events = _fetch(
        requests_mock,
        session,
        {
            "2023 June 01": {(24, "Gas"): 100.0},
            # Autumn: the 01:00 band holds both occurrences of the repeated hour.
            "2023 October 29": {(2, "Gas"): 300.0},
        },
        datetime(2023, 6, 1, tzinfo=UTC),
        datetime(2023, 10, 30, tzinfo=UTC),
    )
    assert {dt: e["production"]["gas"] for dt, e in events.items()} == {
        datetime(2023, 6, 1, 11, tzinfo=UTC): 200.0,  # 12:00 IST
        datetime(2023, 10, 29, 0, tzinfo=UTC): 300.0,  # 01:00 IST
        datetime(2023, 10, 29, 1, tzinfo=UTC): 300.0,  # 01:00 GMT
    }


def test_only_ie_is_covered(session):
    with pytest.raises(ParserException):
        CSO.fetch_production_range(
            ZoneKey("GB-NIR"), session, CSO.MEG01_START, CSO.MEG01_END
        )
