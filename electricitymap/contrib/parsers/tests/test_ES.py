from datetime import datetime

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import ES
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
def mock_response(adapter):
    # The upstream payloads are JSONP-wrapped, not strictly valid JSON.
    for zone_key, filename, target_date in ZONE_FIXTURES:
        with open(f"{MOCKS_DIR}/{filename}", "rb") as data:
            adapter.register_uri(
                GET,
                ES.get_url(zone_key, target_date),
                content=data.read(),
            )


@pytest.mark.parametrize(
    "zone_key,target_date",
    [(z, d) for z, _, d in ZONE_FIXTURES],
    ids=[z for z, _, _ in ZONE_FIXTURES],
)
def test_fetch_consumption(adapter, session, snapshot, zone_key, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_consumption(zone_key, session, datetime.fromisoformat(target_date))


@pytest.mark.parametrize(
    "zone_key,target_date",
    [(z, d) for z, _, d in ZONE_FIXTURES],
    ids=[z for z, _, _ in ZONE_FIXTURES],
)
def test_fetch_production(adapter, session, snapshot, zone_key, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_production(zone_key, session, datetime.fromisoformat(target_date))


@pytest.mark.parametrize(
    "zone_key1,zone_key2,target_date",
    [
        (ZoneKey("ES"), ZoneKey("PT"), "2024-10-26"),
        (ZoneKey("ES-IB-IZ"), ZoneKey("ES-IB-MA"), "2024-10-26"),
        (ZoneKey("ES-CN-FV"), ZoneKey("ES-CN-LZ"), "2026-04-28"),
    ],
    ids=["ES->PT", "ES-IB-IZ->ES-IB-MA", "ES-CN-FV->ES-CN-LZ"],
)
def test_fetch_exchange(adapter, session, snapshot, zone_key1, zone_key2, target_date):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ES.fetch_exchange(
        zone_key1, zone_key2, session, datetime.fromisoformat(target_date)
    )
