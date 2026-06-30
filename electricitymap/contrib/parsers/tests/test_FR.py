import json
import os
import urllib.parse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.FR import API_ENDPOINT, fetch_production
from electricitymap.contrib.types import ZoneKey

MOCK_RESPONSE_PATH = "electricitymap/contrib/parsers/tests/mocks/FR/response.json"
TZ = ZoneInfo("Europe/Paris")


def _load_records() -> list[dict]:
    with open(MOCK_RESPONSE_PATH, "rb") as mock_file:
        return json.load(mock_file)["records"]


def _parse_paris_bound(value: str) -> datetime:
    """Parse a `YYYY-MM-DDTHH:MM` bound (sent by the parser) as Europe/Paris local."""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M").replace(tzinfo=TZ)


def _make_query_aware_callback(records: list[dict]):
    """Build a requests_mock `json=` callback that honours the parser's `q` filter.

    The real parser fetches a *padded* window via the `q` query param
    (``date_heure >= {FROM} AND date_heure <= {TO}``). The existing snapshot
    mock ignores the query and returns every record, so the padding is never
    exercised. This callback filters `records` to the requested instant range,
    which means a record is only returned if the parser actually asked for it —
    making the padded boundary fetch observable.
    """

    def callback(request, context):
        # Parse from the raw URL (not request.qs) to preserve the ISO "T":
        # request.qs lowercases values, which would corrupt "...T01:15".
        query = urllib.parse.parse_qs(urllib.parse.urlparse(request.url).query)
        q = query["q"][0]
        # q looks like: "date_heure >= 2023-09-21T00:45 AND date_heure <= 2023-09-22T01:15"
        from_str, to_str = q.replace("date_heure >= ", "").split(" AND date_heure <= ")
        dt_from = _parse_paris_bound(from_str.strip())
        dt_to = _parse_paris_bound(to_str.strip())

        filtered = [
            record
            for record in records
            if dt_from
            <= datetime.fromisoformat(record["fields"]["date_heure"])
            <= dt_to
        ]
        context.status_code = 200
        return {"records": filtered}

    return callback


def test_production(requests_mock, session, snapshot):
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    with open(MOCK_RESPONSE_PATH, "rb") as mock_file:
        requests_mock.register_uri(
            GET,
            API_ENDPOINT,
            content=mock_file.read(),
        )

    # The mock spans Paris 2023-09-21T02:00 -> 2023-09-22T02:00 (1/4h granularity).
    # This target maps to a Paris window of [2023-09-21 01:00, 2023-09-22 01:00],
    # which sits inside the mock range so every kept 30-min bucket is averaged from
    # both of its quarter-hour points (no partial single-point bucket at the edges).
    assert snapshot == fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
        target_datetime=datetime(2023, 9, 21, 23, 0, tzinfo=timezone.utc),
    )


def test_padding_completes_boundary_bucket(requests_mock, session):
    """The +15min end padding must complete the final 30-min boundary bucket.

    Target Paris window end is 2023-09-22 01:00. The reindex bucket at 01:00 is
    {01:00, 01:15}, but 01:15 is *outside* the requested window (<= 01:00) — it
    is only fetched because of WINDOW_PADDING. With a query-aware mock (which
    returns a record only if the parser actually requested it), the 01:00 bucket
    can only be averaged from both points if the padded fetch pulled in 01:15.

    Trim must then drop the padding so no datapoint with datetime > 01:00 leaks.
    """
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    records = _load_records()

    requests_mock.register_uri(
        GET,
        API_ENDPOINT,
        json=_make_query_aware_callback(records),
    )

    target_datetime = datetime(2023, 9, 21, 23, 0, tzinfo=timezone.utc)
    boundary_dt = datetime(2023, 9, 22, 1, 0, tzinfo=TZ)  # Paris window end

    # Read the raw fuel values straight from the mock so the expectation is faithful.
    by_dt = {
        datetime.fromisoformat(r["fields"]["date_heure"]): r["fields"] for r in records
    }
    gaz_at_0100 = by_dt[datetime(2023, 9, 22, 1, 0, tzinfo=TZ)]["gaz"]
    gaz_at_0115 = by_dt[datetime(2023, 9, 22, 1, 15, tzinfo=TZ)]["gaz"]

    # The two raw points must differ, otherwise the two-point average would be
    # indistinguishable from the single 01:00-only value and would not prove the
    # padded 01:15 point was pulled in.
    assert gaz_at_0100 != gaz_at_0115
    expected_gas_mean = (gaz_at_0100 + gaz_at_0115) / 2

    result = fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
        target_datetime=target_datetime,
    )

    by_result_dt = {dp["datetime"]: dp for dp in result}

    # --- Padding proof -----------------------------------------------------
    # gaz -> gas is a clean 1:1 mapping (no negation, no 3->1 hydro merge), so the
    # stored "gas" value must equal the mean of the 01:00 and 01:15 readings.
    assert boundary_dt in by_result_dt
    boundary_gas = by_result_dt[boundary_dt]["production"]["gas"]
    assert boundary_gas == pytest.approx(expected_gas_mean)
    # And it must NOT equal the single 01:00-only value (would mean no padding).
    assert boundary_gas != pytest.approx(gaz_at_0100)

    # --- Trim proof --------------------------------------------------------
    # The padded 01:15 point fed the 01:00 bucket but must not leak an extra
    # output bucket (e.g. a 01:15 or 01:30 datapoint).
    assert all(dp["datetime"] <= boundary_dt for dp in result)
