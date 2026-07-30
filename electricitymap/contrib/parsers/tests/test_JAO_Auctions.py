import json
import logging
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZoneKey
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers.JAO_Auctions import (
    EM_TO_JAO_ZONE,
    EM_ZONE_TO_JAO_PREFIX,
    JAO_AUCTION_MAX_WINDOW_DAYS,
    fetch_auction_atc_day_ahead,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import AtcType

os.environ["JAO_AUCTION_API_KEY"] = "dummy"

BASE_MOCK_PATH = Path("electricitymap/contrib/parsers/tests/mocks/JAO_Auctions")
ATC_DAY_AHEAD_AUCTION_URL_REGEX = re.compile(r"https://api.jao.eu/OWSMP/getauctions")

# The FR->GB mocks are a real capture covering the 2026-07-28 and 2026-07-29 local
# market days, so the window has to contain them.
TARGET_DATETIME = datetime.fromisoformat("2026-07-28T00:00:00+00:00")

# Real HTTP 400 body returned when a corridor has no auction in the window.
NO_DATA_RESPONSE = {
    "status_code": 400,
    "json": json.loads((BASE_MOCK_PATH / "no-data.json").read_text()),
}


def _mock(filename: str) -> dict:
    return {"json": json.loads((BASE_MOCK_PATH / filename).read_text())}


def test_fetch_auction_atc_day_ahead_fr_gb(requests_mock, session, snapshot):
    """FR->GB sums three interconnectors (IFA1, IFA2, ElecLink) per direction."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            _mock("if1-fr-gb.json"),
            _mock("if1-gb-fr.json"),
            _mock("if2-fr-gb.json"),
            _mock("if2-gb-fr.json"),
            _mock("el1-fr-gb.json"),
            _mock("el1-gb-fr.json"),
        ],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("FR"),
        ZoneKey("GB"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
    assert corridors == [
        "if1-fr-gb",
        "if1-gb-fr",
        "if2-fr-gb",
        "if2-gb-fr",
        "el1-fr-gb",
        "el1-gb-fr",
    ]
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


def test_fetch_auction_atc_day_ahead_window_covers_target_local_day(
    requests_mock, session
):
    """Auctions are stamped at the start of the local market day, which is 22:00/23:00
    UTC the day before, and the API filters on that field. The requested window must
    therefore start before UTC midnight of the target day or it would miss it."""
    requests_mock.register_uri(GET, ATC_DAY_AHEAD_AUCTION_URL_REGEX, **NO_DATA_RESPONSE)

    fetch_auction_atc_day_ahead(
        ZoneKey("CH"),
        ZoneKey("DE"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    query = requests_mock.request_history[0].qs
    assert query["fromdate"][0] == "2026-07-27-00:00:00"

    # The API rejects anything longer than 31 days, so the day of lookback has to come
    # out of the forward span rather than extend the window.
    fromdate = datetime.strptime(query["fromdate"][0], "%Y-%m-%d-%H:%M:%S")
    todate = datetime.strptime(query["todate"][0], "%Y-%m-%d-%H:%M:%S")
    assert todate - fromdate <= timedelta(days=JAO_AUCTION_MAX_WINDOW_DAYS)


def test_fetch_auction_atc_day_ahead_unconfigured_border_raises(requests_mock, session):
    """A border absent from EM_ZONE_TO_JAO_PREFIX is a configuration error, not an
    empty result — guessing a corridor code would silently report no data."""
    requests_mock.register_uri(GET, ATC_DAY_AHEAD_AUCTION_URL_REGEX, json=[])

    with pytest.raises(ParserException, match="No JAO auction corridors configured"):
        fetch_auction_atc_day_ahead(
            ZoneKey("DE"),
            ZoneKey("DK-DK1"),
            session=session,
            target_datetime=TARGET_DATETIME,
        )

    assert requests_mock.request_history == []


def test_fetch_auction_atc_day_ahead_no_data_is_not_an_error(requests_mock, session):
    """The API answers HTTP 400 "No Data found" instead of an empty 200. That must
    yield no events rather than failing the border."""
    requests_mock.register_uri(GET, ATC_DAY_AHEAD_AUCTION_URL_REGEX, **NO_DATA_RESPONSE)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("CH"),
        ZoneKey("FR"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
    assert corridors == ["ch-fr", "fr-ch"]
    assert result == []


def test_fetch_auction_atc_day_ahead_http_error_still_raises(requests_mock, session):
    """Only 400 "No Data found" is benign; other failures must surface."""
    requests_mock.register_uri(
        GET, ATC_DAY_AHEAD_AUCTION_URL_REGEX, status_code=500, text="boom"
    )

    with pytest.raises(ParserException, match="HTTP 500"):
        fetch_auction_atc_day_ahead(
            ZoneKey("CH"),
            ZoneKey("DE"),
            session=session,
            target_datetime=TARGET_DATETIME,
        )


def test_fetch_auction_atc_day_ahead_em_to_jao_zone_remap(requests_mock, session):
    """DK-DK1 must be remapped to D1 in corridor names (the Publication Tool uses DK1).
    Export corridor is VKL-D1-GB, import corridor is VKL-GB-D1."""
    auction = {
        "identification": "VKL-TEST",
        "marketPeriodStart": "2026-07-27T22:00:00.000+00:00",
        "marketPeriodStop": "2026-07-27T23:00:00.000+00:00",
        "results": [{"productHour": "00:00-01:00", "offeredCapacity": 2500}],
    }
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {"json": [auction]},
            {
                "json": [
                    {
                        **auction,
                        "results": [{**auction["results"][0], "offeredCapacity": 2200}],
                    }
                ]
            },
        ],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("DK-DK1"),
        ZoneKey("GB"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
    assert corridors == ["vkl-d1-gb", "vkl-gb-d1"]
    assert result == [
        {
            "datetime": datetime(2026, 7, 27, 22, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2026, 7, 27, 23, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "DK-DK1->GB",
            "capacityExport": 2500.0,
            "capacityImport": 2200.0,
            "atcType": AtcType.COORDINATED_NTC,
            "source": "jao.eu",
            "sourceType": EventSourceType.published,
        }
    ]


def test_wired_borders_match_configured_corridors():
    """The parser's border list and the `atcDayAhead` wiring must stay in step.

    A border wired in config but missing from EM_ZONE_TO_JAO_PREFIX raises at runtime
    on every run; a border in the mapping with no config is dead code. Neither is
    visible without cross-checking, so pin it here.
    """
    wired = {
        key
        for key, config in EXCHANGES_CONFIG.items()
        if "JAO_Auctions" in str((config.get("parsers") or {}).get("atcDayAhead", ""))
    }
    assert wired == set(EM_ZONE_TO_JAO_PREFIX)


def test_fetch_auction_atc_day_ahead_italian_zone_remaps(requests_mock, session):
    """JAO reuses one "IT" code for every Italian border and lets the counterparty
    disambiguate the bidding zone, so both Italian borders must collapse to it: the
    Swiss interconnector lands in Italy North, MONITA to Montenegro in Italy
    Centre-South. Without the remap these would request the nonexistent corridors
    CH-IT-NO and IT-CSO-ME."""
    requests_mock.register_uri(GET, ATC_DAY_AHEAD_AUCTION_URL_REGEX, **NO_DATA_RESPONSE)

    for zone_a, zone_b, expected in [
        ("CH", "IT-NO", ["ch-it", "it-ch"]),
        ("IT-CSO", "ME", ["it-me", "me-it"]),
    ]:
        requests_mock.reset()
        fetch_auction_atc_day_ahead(
            ZoneKey(zone_a),
            ZoneKey(zone_b),
            session=session,
            target_datetime=TARGET_DATETIME,
        )
        corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
        assert corridors == expected, f"{zone_a}->{zone_b}"


def test_fetch_auction_atc_day_ahead_unprefixed_borders_are_configured(
    requests_mock, session
):
    """Every unprefixed border must resolve to a corridor pair the API actually serves,
    which for these is simply "{FROM}-{TO}" after zone remapping."""
    requests_mock.register_uri(GET, ATC_DAY_AHEAD_AUCTION_URL_REGEX, **NO_DATA_RESPONSE)

    unprefixed = [b for b, p in EM_ZONE_TO_JAO_PREFIX.items() if p == [""]]
    assert len(unprefixed) == 14

    for border in unprefixed:
        requests_mock.reset()
        zone_a, zone_b = border.split("->")
        fetch_auction_atc_day_ahead(
            ZoneKey(zone_a),
            ZoneKey(zone_b),
            session=session,
            target_datetime=TARGET_DATETIME,
        )
        jao_a = EM_TO_JAO_ZONE.get(zone_a, zone_a).lower()
        jao_b = EM_TO_JAO_ZONE.get(zone_b, zone_b).lower()
        corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
        assert corridors == [f"{jao_a}-{jao_b}", f"{jao_b}-{jao_a}"], border


def test_fetch_auction_atc_day_ahead_one_sided_export(requests_mock, session):
    """When only the export corridor (CH-DE) has an auction and the import corridor
    (DE-CH) returns "No Data found", capacityImport should be None."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {
                "json": [
                    {
                        "identification": "CH-DE-TEST",
                        "marketPeriodStart": "2026-07-27T22:00:00.000+00:00",
                        "marketPeriodStop": "2026-07-27T23:00:00.000+00:00",
                        "results": [
                            {"productHour": "00:00-01:00", "offeredCapacity": 3620}
                        ],
                    }
                ]
            },
            NO_DATA_RESPONSE,
        ],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("CH"),
        ZoneKey("DE"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
    assert corridors == ["ch-de", "de-ch"]
    assert result == [
        {
            "datetime": datetime(2026, 7, 27, 22, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2026, 7, 27, 23, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "CH->DE",
            "capacityExport": 3620.0,
            "capacityImport": None,
            "atcType": AtcType.COORDINATED_NTC,
            "source": "jao.eu",
            "sourceType": EventSourceType.published,
        }
    ]


def test_fetch_auction_atc_day_ahead_import_only_and_zone_key_ordering(
    requests_mock, session
):
    """Zone keys are sorted internally so GB+DK-DK1 must produce the same
    sortedZoneKeys as DK-DK1+GB. Also exercises the import-only path
    (capacityExport=None) as the symmetric counterpart to one_sided_export."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            NO_DATA_RESPONSE,  # vkl-d1-gb (export) — no auction
            {
                "json": [
                    {
                        "identification": "VKL-GB-D1-TEST",
                        "marketPeriodStart": "2026-07-27T22:00:00.000+00:00",
                        "marketPeriodStop": "2026-07-27T23:00:00.000+00:00",
                        "results": [
                            {"productHour": "00:00-01:00", "offeredCapacity": 1800}
                        ],
                    }
                ]
            },
        ],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("GB"),  # reversed argument order vs em_to_jao_zone_remap
        ZoneKey("DK-DK1"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert result == [
        {
            "datetime": datetime(2026, 7, 27, 22, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2026, 7, 27, 23, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "DK-DK1->GB",
            "capacityExport": None,
            "capacityImport": 1800.0,
            "atcType": AtcType.COORDINATED_NTC,
            "source": "jao.eu",
            "sourceType": EventSourceType.published,
        }
    ]


def test_fetch_auction_atc_day_ahead_long_dst_day(requests_mock, session):
    """Real 2025-10-26 capture: the local day has 25 hours and the repeated hour is
    labelled "02:00-03:00*". Deriving the offset from the label would collapse it onto
    its twin and sum both capacities, losing an hour and doubling a value."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[_mock("dst-long-if1-fr-gb.json"), NO_DATA_RESPONSE],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("FR"),
        ZoneKey("GB"),
        session=session,
        target_datetime=datetime.fromisoformat("2025-10-26T00:00:00+00:00"),
    )

    datetimes = [event["datetime"] for event in result]
    assert len(datetimes) == 25
    assert datetimes == sorted(datetimes)
    assert max(Counter(datetimes).values()) == 1
    # The market day runs 22:00Z 10-25 → 23:00Z 10-26, contiguous throughout.
    assert datetimes[0] == datetime(2025, 10, 25, 22, tzinfo=timezone.utc)
    assert datetimes[-1] == datetime(2025, 10, 26, 22, tzinfo=timezone.utc)
    assert result[-1]["end_datetime"] == datetime(2025, 10, 26, 23, tzinfo=timezone.utc)
    # The corridor offered a flat 556 MW all day, so any collision between
    # "02:00-03:00" and "02:00-03:00*" would show up as a doubled 1112 MW. The
    # repeated hour lands at 01:00Z, right after its twin at 00:00Z.
    assert {event["capacityExport"] for event in result} == {556.0}
    assert datetime(2025, 10, 26, 0, tzinfo=timezone.utc) in datetimes
    assert datetime(2025, 10, 26, 1, tzinfo=timezone.utc) in datetimes


def test_fetch_auction_atc_day_ahead_short_dst_day(requests_mock, session):
    """Real 2026-03-28→31 capture spanning the 23-hour local day. Label-derived offsets
    would shift every post-transition hour and make 03-28's last product collide with
    03-29's first, summing two unrelated hours into one fabricated value."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[_mock("dst-short-if1-fr-gb.json"), NO_DATA_RESPONSE],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("FR"),
        ZoneKey("GB"),
        session=session,
        target_datetime=datetime.fromisoformat("2026-03-29T00:00:00+00:00"),
    )

    datetimes = [event["datetime"] for event in result]
    # 23 + 24 + 24 hourly products across three market days, none colliding.
    assert len(datetimes) == 71
    assert max(Counter(datetimes).values()) == 1
    assert datetimes == sorted(datetimes)
    # Contiguous hourly coverage with no gap at the transition.
    assert datetimes[-1] - datetimes[0] == timedelta(hours=70)
    assert all(
        later - earlier == timedelta(hours=1)
        for earlier, later in zip(datetimes, datetimes[1:], strict=False)
    )


def test_fetch_auction_atc_day_ahead_ignores_not_yet_held_auctions(
    requests_mock, session, caplog
):
    """The window reaches ~30 days forward, so most auctions in it are announced but not
    yet held and carry no results. That is routine and must not be logged as an error."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {
                "json": [
                    {
                        "identification": "CH-DE-HELD",
                        "marketPeriodStart": "2026-07-27T22:00:00.000+00:00",
                        "marketPeriodStop": "2026-07-27T23:00:00.000+00:00",
                        "results": [
                            {"productHour": "00:00-01:00", "offeredCapacity": 1500}
                        ],
                    },
                    {
                        "identification": "CH-DE-UPCOMING",
                        "marketPeriodStart": "2026-08-20T22:00:00.000+00:00",
                        "marketPeriodStop": "2026-08-21T22:00:00.000+00:00",
                        "results": [],
                    },
                ]
            },
            NO_DATA_RESPONSE,
        ],
    )

    with caplog.at_level(logging.ERROR):
        result = fetch_auction_atc_day_ahead(
            ZoneKey("CH"),
            ZoneKey("DE"),
            session=session,
            target_datetime=TARGET_DATETIME,
        )

    assert [event["capacityExport"] for event in result] == [1500.0]
    assert caplog.records == []


def test_fetch_auction_atc_day_ahead_skips_auction_not_tiling_market_period(
    requests_mock, session
):
    """Offsets are positional, so an auction whose products don't tile its market
    period is skipped rather than emitted on guessed timestamps."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {
                "json": [
                    {
                        "identification": "CH-DE-PARTIAL",
                        "marketPeriodStart": "2026-07-27T22:00:00.000+00:00",
                        "marketPeriodStop": "2026-07-28T22:00:00.000+00:00",  # 24h
                        "results": [
                            {"productHour": "00:00-01:00", "offeredCapacity": 100},
                            {"productHour": "01:00-02:00", "offeredCapacity": 200},
                        ],
                    }
                ]
            },
            NO_DATA_RESPONSE,
        ],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("CH"),
        ZoneKey("DE"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert result == []
