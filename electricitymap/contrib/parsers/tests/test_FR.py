import json
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time
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


# Pin "now" to the end of the mock window (Paris 2023-09-22 02:00 == 00:00 UTC) so
# the default no-`target_datetime` path produces a requested window of
# [2023-09-21 02:00, 2023-09-22 02:00] that fully contains the mock data. Without
# this the window-edge trim (relative to the real clock) would drop every 2023
# bucket and leave an empty result.
@freeze_time("2023-09-22 00:00:00")
def test_production(requests_mock, session, snapshot):
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    with open(
        "electricitymap/contrib/parsers/tests/mocks/FR/response.json", "rb"
    ) as mock_file:
        requests_mock.register_uri(
            GET,
            API_ENDPOINT,
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
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


def test_no_churn_across_shifting_window_edges(requests_mock, session):
    """A timestamp's stored value must not depend on where the fetch edge fell.

    This is the property the padding exists to guarantee. A 30-min bucket is the
    mean of its two quarter-hour points (T and T+15); if the fetch window edge
    lands *between* them, the bucket is averaged from one point on one refetch
    and from two on the next, so its stored value flips back and forth (churn).

    We refetch the same data at five window ends that all fall in the 01:00
    bucket's half-hour but at different sub-30-min offsets (:00, :07, :15, :22,
    :29 past 01:00 Paris == 23:00Z + those minutes). With a query-aware mock, an
    edge only pulls in 01:15 if the parser actually requested it — so without the
    padding the 01:00 bucket would be single-point for the :00 edge and two-point
    for the later ones. Every timestamp shared across refetches must be identical.
    """
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    records = _load_records()
    requests_mock.register_uri(
        GET,
        API_ENDPOINT,
        json=_make_query_aware_callback(records),
    )

    # UTC = Paris - 2h (CEST), so Paris 2023-09-22 01:00 == 2023-09-21 23:00Z.
    edges = [
        datetime(2023, 9, 21, 23, minute, tzinfo=timezone.utc)
        for minute in (0, 7, 15, 22, 29)
    ]
    per_edge = [
        {
            dp["datetime"]: dp
            for dp in fetch_production(
                zone_key=ZoneKey("FR"), session=session, target_datetime=edge
            )
        }
        for edge in edges
    ]

    # The 01:00 boundary bucket is retained by all five edges (01:00 <= end < 01:30)
    # and is the one whose composition the moving edge would otherwise change.
    boundary_dt = datetime(2023, 9, 22, 1, 0, tzinfo=TZ)
    assert all(boundary_dt in by_dt for by_dt in per_edge)

    # Every timestamp present in more than one refetch must carry an identical
    # datapoint regardless of the window edge — i.e. no churn.
    for ts in set().union(*per_edge):
        seen = [by_dt[ts] for by_dt in per_edge if ts in by_dt]
        assert all(dp == seen[0] for dp in seen), f"churn at {ts}: {seen}"


def test_window_advances_in_15min_steps_without_churn(requests_mock, session, snapshot):
    """Stepping the window end by 15 min must only *append* — never rewrite.

    15-min steps are the strict test: ends landing on :15/:45 fall *inside* an
    incomplete 30-min boundary bucket, exactly where churn would strike (the 30-min
    step skips those positions). We snapshot the 01:00 window as a full base, then
    snapshot each 15-min-advanced window as a ``diff`` against it. Keyed by
    datetime, the recorded diffs read as a clean, reviewable progression:

    * +15 (01:15) -> *empty* diff: advancing into the middle of the 01:00 bucket
      changes nothing — the padding already gave it the two-point mean (906).
    * +30 (01:30) -> single addition (+01:30): the bucket completed, one new point.
    * +45 (01:45) -> same diff as 01:30: another mid-bucket no-op.
    * +60 (02:00) -> adds +02:00.

    The base pins every bucket's value; the diffs pin the *relationship* between
    windows. A padding regression turns an empty mid-bucket diff into a
    *modification* of an already-emitted bucket (e.g. 01:00 flipping 906 -> 1100),
    visible in the .ambr git diff and failing this test until regenerated.

    Regenerate with ``pytest --snapshot-update`` after an intentional mock change;
    a correct parser keeps every mid-bucket diff empty and every step append-only.
    """
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    records = _load_records()
    requests_mock.register_uri(
        GET,
        API_ENDPOINT,
        json=_make_query_aware_callback(records),
    )

    # Paris 01:00 == 23:00Z (CEST = UTC+2); each step advances the window end 15 min.
    base_end = datetime(2023, 9, 21, 23, 0, tzinfo=timezone.utc)

    def fetch_by_dt(step_minutes: int) -> dict:
        return {
            dp["datetime"]: dp
            for dp in fetch_production(
                zone_key=ZoneKey("FR"),
                session=session,
                target_datetime=base_end + timedelta(minutes=step_minutes),
            )
        }

    assert fetch_by_dt(0) == snapshot(name="end_0100")
    assert fetch_by_dt(15) == snapshot(name="end_0115", diff="end_0100")
    assert fetch_by_dt(30) == snapshot(name="end_0130", diff="end_0100")
    assert fetch_by_dt(45) == snapshot(name="end_0145", diff="end_0100")
    assert fetch_by_dt(60) == snapshot(name="end_0200", diff="end_0100")
