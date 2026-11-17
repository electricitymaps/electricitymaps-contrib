from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import ES
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

MOCKS_DIR = "electricitymap/contrib/parsers/tests/mocks/ES"

# (zone_key, mock_filename, target_date) — one row per upstream system response.
ZONE_FIXTURES = [
    (ZoneKey("ES"), "demandaGeneracionPeninsula.json", "2024-10-26"),
    (ZoneKey("ES-IB-MA"), "demandaGeneracionBaleares.json", "2024-10-26"),
    (ZoneKey("ES-CN-TE"), "demandaGeneracionCanarias.json", "2024-10-26"),
    (ZoneKey("ES-CN-LZ"), "demandaGeneracionCanariasLanzarote.json", "2026-04-28"),
    (ZoneKey("ES-CE"), "demandaGeneracionPeninsulaCeuta.json", "2026-04-21"),
]


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    # The upstream payloads are JSONP-wrapped, not strictly valid JSON.
    for zone_key, filename, target_date in ZONE_FIXTURES:
        with open(f"{MOCKS_DIR}/{filename}", "rb") as data:
            requests_mock.register_uri(
                GET,
                ES.get_url(zone_key, target_date),
                content=data.read(),
            )

    with open(f"{MOCKS_DIR}/demandaGeneracionCanariasLaGomera.json", "rb") as data:
        requests_mock.register_uri(
            GET,
            ES.get_url(ZoneKey("ES-CN-IG"), "2026-08-01"),
            content=data.read(),
        )


@pytest.mark.parametrize(
    "zone_key,target_date",
    [(z, d) for z, _, d in ZONE_FIXTURES],
    ids=[z for z, _, _ in ZONE_FIXTURES],
)
def test_fetch_consumption(requests_mock, session, snapshot, zone_key, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_consumption(zone_key, session, datetime.fromisoformat(target_date))


@pytest.mark.parametrize(
    "zone_key,target_date",
    [(z, d) for z, _, d in ZONE_FIXTURES],
    ids=[z for z, _, _ in ZONE_FIXTURES],
)
def test_fetch_production(requests_mock, session, snapshot, zone_key, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_production(zone_key, session, datetime.fromisoformat(target_date))


@pytest.mark.parametrize(
    "zone_key1,zone_key2,target_date",
    [
        (ZoneKey("AD"), ZoneKey("ES"), "2024-10-26"),
        (ZoneKey("ES"), ZoneKey("PT"), "2024-10-26"),
        (ZoneKey("ES-IB-IZ"), ZoneKey("ES-IB-MA"), "2024-10-26"),
        (ZoneKey("ES-CN-FV"), ZoneKey("ES-CN-LZ"), "2026-04-28"),
        (ZoneKey("ES-CN-IG"), ZoneKey("ES-CN-TE"), "2026-08-01"),
    ],
    ids=[
        "AD->ES",
        "ES->PT",
        "ES-IB-IZ->ES-IB-MA",
        "ES-CN-FV->ES-CN-LZ",
        "ES-CN-IG->ES-CN-TE",
    ],
)
def test_fetch_exchange(
    requests_mock, session, snapshot, zone_key1, zone_key2, target_date
):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_exchange(
        zone_key1, zone_key2, session, datetime.fromisoformat(target_date)
    )


def test_fetch_exchange_ad_es_ignores_ree_sign(monkeypatch, session):
    """REE has published the Spain -> Andorra flow both as positive impAnd and
    as negative expAnd. Both must map to Spain -> Andorra (negative AD->ES), and
    points where both keys are non-zero are glitches that must be dropped."""
    tz = ZoneInfo("Europe/Madrid")
    events = [
        {"ts": datetime(2026, 11, 14, 0, 0, tzinfo=tz), "impAnd": 30, "expAnd": 0},
        {"ts": datetime(2026, 11, 14, 0, 5, tzinfo=tz), "impAnd": 0, "expAnd": -30},
        {
            "ts": datetime(2026, 11, 14, 0, 10, tzinfo=tz),
            "impAnd": 3942,
            "expAnd": -3942,
        },
        {"ts": datetime(2026, 11, 14, 0, 15, tzinfo=tz), "impAnd": 0, "expAnd": 0},
    ]
    monkeypatch.setattr(ES, "fetch_and_preprocess_data", lambda *args: events)

    exchanges = ES.fetch_exchange(
        ZoneKey("ES"), ZoneKey("AD"), session, datetime(2026, 11, 14, tzinfo=tz)
    )

    assert [(e["datetime"].minute, e["netFlow"]) for e in exchanges] == [
        (0, -30),
        (5, -30),
        (15, 0),
    ]
    assert all(e["sortedZoneKeys"] == "AD->ES" for e in exchanges)


def test_fetch_exchange_ad_es_before_start_raises(session):
    with pytest.raises(ParserException, match="before 2024-09-20"):
        ES.fetch_exchange(
            ZoneKey("AD"), ZoneKey("ES"), session, datetime(2024, 9, 19, 23, 59)
        )
