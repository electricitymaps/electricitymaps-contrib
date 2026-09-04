import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZoneKey
from electricitymap.contrib.parsers.BRITNED import (
    BRITNED_EXCHANGE_KEY,
    BRITNED_MAX_FETCH_DAYS,
    _target_window,
    fetch_auction_atc_day_ahead,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import AtcType

BASE_MOCK_PATH = Path("electricitymap/contrib/parsers/tests/mocks/BRITNED")
LIST_URL_REGEX = re.compile(
    r"https://api\.empire\.britned\.com/v1/public/allocated-auctions"
)
DETAIL_URL_REGEX = re.compile(
    r"https://api\.empire\.britned\.com/v1/public/auctions/day-ahead/"
)

# The mocks are a real capture of the 2026-08-28 CEST market day, which runs
# 2026-08-27T22:00Z -> 2026-08-28T22:00Z.
TARGET_DATETIME = datetime.fromisoformat("2026-08-28T00:00:00+00:00")
GB_NL_AUCTION_ID = "3966cbc6-0e79-4bda-82ab-991a2ad68c3f"
NL_GB_AUCTION_ID = "1ca87bd6-2622-4b56-afeb-9a759e9dc2c7"


def _load(filename: str) -> dict:
    return json.loads((BASE_MOCK_PATH / filename).read_text())


def _mock(filename: str) -> dict:
    return {"json": _load(filename)}


def _register_happy_path(requests_mock):
    """List returns both directions; each detail id serves its own capture.

    Registering the detail mocks per-URL rather than as an ordered `response_list`
    keeps the test honest about *which* auction each response belongs to — an
    export/import mix-up would otherwise still pass.
    """
    requests_mock.register_uri(GET, LIST_URL_REGEX, **_mock("allocated-auctions.json"))
    for auction_id, filename in (
        (GB_NL_AUCTION_ID, "auction-gb-nl.json"),
        (NL_GB_AUCTION_ID, "auction-nl-gb.json"),
    ):
        requests_mock.register_uri(
            GET,
            f"https://api.empire.britned.com/v1/public/auctions/day-ahead/{auction_id}",
            **_mock(filename),
        )


def test_fetch_auction_atc_day_ahead(requests_mock, session, snapshot):
    """One delivery day yields one event per MTU carrying both directions."""
    _register_happy_path(requests_mock)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


def test_fetch_auction_atc_day_ahead_reads_final_oc_in_mw(requests_mock, session):
    """Empire reports kW; events must be MW.

    Also pins that `finalOc` is the source field, not the sibling `atc`. `atc` is 0
    for every MTU in the capture — reading it would report a permanently closed
    border while looking superficially fine.
    """
    _register_happy_path(requests_mock)
    capture = _load("auction-gb-nl.json")
    assert {mtu["atc"] for mtu in capture["mtus"]} == {0}, "capture should pin atc == 0"
    expected_first = capture["mtus"][0]["finalOc"] / 1000

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    assert result[0]["capacityExport"] == expected_first
    assert 100 < result[0]["capacityExport"] < 2000, "should be MW, not kW"
    assert all(event["capacityExport"] for event in result)


def test_fetch_auction_atc_day_ahead_maps_directions(requests_mock, session):
    """GB_NL is the export leg of the sorted "GB->NL" key, NL_GB the import leg."""
    _register_happy_path(requests_mock)
    gb_nl = {m["mtu"]: m["finalOc"] / 1000 for m in _load("auction-gb-nl.json")["mtus"]}
    nl_gb = {m["mtu"]: m["finalOc"] / 1000 for m in _load("auction-nl-gb.json")["mtus"]}
    # The two captures must differ somewhere, or this test cannot detect a swap.
    assert gb_nl != nl_gb

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    for event in result:
        key = event["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")
        assert event["capacityExport"] == gb_nl[key]
        assert event["capacityImport"] == nl_gb[key]


def test_fetch_auction_atc_day_ahead_is_cross_netted(requests_mock, session):
    """The two directions sum to well over the cable rating, which is the whole
    reason this border is tagged EXPLICIT_AUCTION.

    BritNed cross-nets, so a single direction is not a bound on physical flow — the
    published GB->NL value can exceed the cable's own rating. If this ever stops
    holding, the `(export + import) / 2` envelope consumers apply needs revisiting,
    so pin it rather than leave it as prose in the docstring.
    """
    _register_happy_path(requests_mock)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    sums = [e["capacityExport"] + e["capacityImport"] for e in result]
    assert min(sums) > 1500, "cross-netted directions should far exceed a ~1000MW cable"
    assert all(e["atcType"] == AtcType.EXPLICIT_AUCTION for e in result)


def test_fetch_auction_atc_day_ahead_zone_order_is_normalised(requests_mock, session):
    """Argument order must not change the emitted key or the direction mapping."""
    _register_happy_path(requests_mock)

    forward = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )
    reversed_ = fetch_auction_atc_day_ahead(
        ZoneKey("NL"), ZoneKey("GB"), session=session, target_datetime=TARGET_DATETIME
    )

    assert forward == reversed_
    assert all(e["sortedZoneKeys"] == BRITNED_EXCHANGE_KEY for e in forward)


def test_fetch_auction_atc_day_ahead_window_covers_target_market_day(
    requests_mock, session
):
    """The requested window must intersect the target day's market day.

    Market days start at CET/CEST midnight — 22:00 UTC (summer) or 23:00 UTC (winter)
    on the *preceding* calendar day — so the window's lower bound sits inside, not at
    the start of, the period we want. That is only safe because Empire's
    delivery-period filter matches on overlap; the assertion below encodes the
    intersection that has to hold, so it would still catch a regression that moved the
    bound past the market day's end.
    """
    requests_mock.register_uri(
        GET, LIST_URL_REGEX, **_mock("allocated-auctions-empty.json")
    )

    fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    query = requests_mock.request_history[0].qs
    assert query["deliveryperiodstart"][0] == "2026-08-28t00:00:00z"
    start = datetime.fromisoformat(
        query["deliveryperiodstart"][0].upper().replace("Z", "+00:00")
    )
    end = datetime.fromisoformat(
        query["deliveryperiodend"][0].upper().replace("Z", "+00:00")
    )
    # The 2026-08-28 market day, as captured in the mocks.
    market_day_start = datetime.fromisoformat("2026-08-27T22:00:00+00:00")
    market_day_end = datetime.fromisoformat("2026-08-28T22:00:00+00:00")
    assert start < market_day_end and end > market_day_start, (
        "window must overlap the target market day"
    )


def test_fetch_auction_atc_day_ahead_no_auctions_returns_empty(requests_mock, session):
    """A cancelled or not-yet-published day is routine, not an error."""
    requests_mock.register_uri(
        GET, LIST_URL_REGEX, **_mock("allocated-auctions-empty.json")
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    assert result == []
    # No auctions listed means no detail calls should have been attempted.
    assert len(requests_mock.request_history) == 1


def test_fetch_auction_atc_day_ahead_single_direction(requests_mock, session):
    """If only one direction's auction ran, emit events with the other side None
    rather than dropping the MTU."""
    listing = _load("allocated-auctions.json")
    listing["entries"] = [
        e for e in listing["entries"] if e["borderDirection"] == "GB_NL"
    ]
    listing["totalCount"] = 1
    requests_mock.register_uri(GET, LIST_URL_REGEX, json=listing)
    requests_mock.register_uri(GET, DETAIL_URL_REGEX, **_mock("auction-gb-nl.json"))

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    assert result, "a one-sided day should still produce events"
    assert all(e["capacityExport"] is not None for e in result)
    assert all(e["capacityImport"] is None for e in result)


def test_fetch_auction_atc_day_ahead_unsupported_border_raises(requests_mock, session):
    """Empire serves only GB<->NL. Any other border is a wiring mistake and must fail
    loudly rather than silently return nothing."""
    with pytest.raises(ParserException, match="only serves GB->NL"):
        fetch_auction_atc_day_ahead(
            ZoneKey("FR"),
            ZoneKey("GB"),
            session=session,
            target_datetime=TARGET_DATETIME,
        )
    assert not requests_mock.request_history


def test_fetch_auction_atc_day_ahead_http_error_raises(requests_mock, session):
    """Unlike JAO, Empire has no "no data" error body — a non-200 is a real failure."""
    requests_mock.register_uri(GET, LIST_URL_REGEX, status_code=503, text="nope")

    with pytest.raises(ParserException, match="HTTP 503"):
        fetch_auction_atc_day_ahead(
            ZoneKey("GB"),
            ZoneKey("NL"),
            session=session,
            target_datetime=TARGET_DATETIME,
        )


def test_britned_border_is_wired_in_config():
    """The parser's single border and the `atcDayAhead` wiring must stay in step: a
    config entry pointing at a border BRITNED refuses is a runtime error on every run,
    and the parser existing unwired is dead code."""
    wired = {
        key
        for key, config in EXCHANGES_CONFIG.items()
        if "BRITNED" in str((config.get("parsers") or {}).get("atcDayAhead", ""))
    }
    assert wired == {BRITNED_EXCHANGE_KEY}


def test_mtu_duration_follows_allocation_mtu_size(requests_mock, session):
    """Event duration comes from the auction's own `allocationMtuSize`, so a switch
    to 15-minute MTUs does not silently emit hour-long events."""
    quarter_hourly = _load("auction-gb-nl.json")
    quarter_hourly["allocationMtuSize"] = "MTU_15_MINS"
    requests_mock.register_uri(GET, LIST_URL_REGEX, **_mock("allocated-auctions.json"))
    requests_mock.register_uri(GET, DETAIL_URL_REGEX, json=quarter_hourly)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    event = result[0]
    assert event["end_datetime"] - event["datetime"] == timedelta(minutes=15)


def test_unknown_mtu_size_is_skipped(requests_mock, session, caplog):
    """An unrecognised MTU size must not be guessed at — timestamps would be wrong."""
    broken = _load("auction-gb-nl.json")
    broken["allocationMtuSize"] = "MTU_7_MINS"
    requests_mock.register_uri(GET, LIST_URL_REGEX, **_mock("allocated-auctions.json"))
    requests_mock.register_uri(GET, DETAIL_URL_REGEX, json=broken)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    assert result == []
    assert "MTU_7_MINS" in caplog.text


def test_timestamps_are_utc_aware(requests_mock, session):
    """Empire stamps its MTUs with a `Z` suffix that `fromisoformat` cannot parse
    before Python 3.11; the parser normalises it, so events must come out tz-aware."""
    _register_happy_path(requests_mock)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"), ZoneKey("NL"), session=session, target_datetime=TARGET_DATETIME
    )

    assert all(e["datetime"].tzinfo is not None for e in result)
    assert result[0]["datetime"] == datetime(2026, 8, 27, 22, 0, tzinfo=timezone.utc), (
        "market day should start at 22:00Z in summer, not UTC midnight"
    )


# --- Fetch-window / refetch coverage -----------------------------------------------
#
# Empire's delivery-period filter matches on overlap (half-open: touching a bound does
# not count), and the detail endpoint returns a whole auction regardless of how little
# of it the window covered. So the property that matters for coverage is simply
# "does the window intersect the market day", never "does it contain it".


def _market_day(date_, utc_offset_hours: int) -> tuple[datetime, datetime]:
    """The CET/CEST market day for a calendar date, expressed in UTC.

    BritNed days run local midnight to local midnight, so in UTC they start 22:00 the
    previous day under CEST (+2) and 23:00 under CET (+1).
    """
    start = datetime(
        date_.year, date_.month, date_.day, tzinfo=timezone.utc
    ) - timedelta(hours=utc_offset_hours)
    return start, start + timedelta(hours=24)


def _overlaps(window: tuple[datetime, datetime], period: tuple[datetime, datetime]):
    return window[0] < period[1] and window[1] > period[0]


def test_refetch_frequency_matches_fetch_window_span():
    """The declared refetch frequency and the window actually requested must agree.

    The framework steps `target_datetime` by REFETCH_FREQUENCY and assumes each call
    returns that much data. If the window were shorter than the step, every refetch
    would leave an unfetched hole; if longer, it would silently re-request. Both
    derive from BRITNED_MAX_FETCH_DAYS today — this pins that they stay in step.
    """
    start, end = _target_window(datetime(2026, 8, 26, 15, 47, tzinfo=timezone.utc))

    assert end - start == timedelta(days=BRITNED_MAX_FETCH_DAYS)
    assert end - start == fetch_auction_atc_day_ahead.REFETCH_FREQUENCY


@pytest.mark.parametrize(
    ("label", "base", "utc_offset"),
    [
        ("summer CEST", datetime(2026, 8, 26, tzinfo=timezone.utc), 2),
        ("winter CET", datetime(2026, 1, 15, tzinfo=timezone.utc), 1),
    ],
)
def test_refetch_chunks_tile_market_days_without_gap(label, base, utc_offset):
    """Consecutive refetch chunks must leave no market day unfetched.

    Chunks abut exactly (chunk N ends where chunk N+1 begins) and the filter excludes
    boundary-touching, so the risk is a market day straddling a chunk boundary being
    dropped by both. It is not — a 24h period always intersects one of two abutting
    7-day windows — but that is exactly the kind of off-by-one worth pinning.
    """
    step = fetch_auction_atc_day_ahead.REFETCH_FREQUENCY
    windows = [_target_window(base + step * i) for i in range(3)]

    # Chunks must be contiguous: no time between one ending and the next starting.
    # strict=False: pairwise iteration, so the second sequence is one shorter.
    for earlier, later in zip(windows, windows[1:], strict=False):
        assert later[0] <= earlier[1], f"{label}: gap between refetch chunks"

    # Every market day inside the covered span must land in at least one chunk.
    covered_until = windows[-1][1]
    day = base.date()
    while (
        datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc) < covered_until
    ):
        period = _market_day(day, utc_offset)
        assert any(_overlaps(w, period) for w in windows), (
            f"{label}: market day {day} fetched by no chunk"
        )
        day += timedelta(days=1)


@pytest.mark.parametrize(
    ("label", "base", "utc_offset"),
    [
        ("summer CEST", datetime(2026, 8, 26, tzinfo=timezone.utc), 2),
        ("winter CET", datetime(2026, 1, 15, tzinfo=timezone.utc), 1),
    ],
)
@pytest.mark.parametrize("hour", range(24))
def test_continuous_mode_window_reaches_next_market_day(label, base, utc_offset, hour):
    """Whatever time of day continuous mode runs, it must reach tomorrow's auction.

    In continuous mode the window's lower bound is UTC midnight of *today*, but the
    market day it needs to reach starts at 22:00 or 23:00 UTC on the preceding
    calendar day. Getting that relationship wrong would clip hours off the day-ahead
    result — the whole point of the parser — and would do so silently, since a short
    day looks like a normal partial publication.
    """
    window = _target_window(base.replace(hour=hour))

    today = _market_day(base.date(), utc_offset)
    tomorrow = _market_day((base + timedelta(days=1)).date(), utc_offset)
    assert _overlaps(window, today), f"{label} {hour:02d}h: misses today's market day"
    assert _overlaps(window, tomorrow), (
        f"{label} {hour:02d}h: misses tomorrow's market day"
    )


def test_continuous_mode_defaults_to_now():
    """`target_datetime=None` must anchor on today, not raise or drift to epoch."""
    start, end = _target_window(None)
    now = datetime.now(tz=timezone.utc)

    assert start <= now < end
    assert start == datetime.combine(
        now.date(), datetime.min.time(), tzinfo=timezone.utc
    )


def test_naive_target_datetime_is_treated_as_utc():
    """A naive datetime must not blow up or be read in local time."""
    naive = _target_window(datetime(2026, 8, 26, 15, 47))
    aware = _target_window(datetime(2026, 8, 26, 15, 47, tzinfo=timezone.utc))

    assert naive == aware
