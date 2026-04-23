import json
import re
from datetime import datetime
from pathlib import Path

from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.parsers.JAO import (
    fetch_core_external_atc_day_ahead,
    fetch_shadow_auction_atc_day_ahead,
)

BASE_MOCK_PATH = Path("electricitymap/contrib/parsers/tests/mocks/JAO")
SHADOW_AUCTION_ATC_URL_REGEX = re.compile(
    r"https://publicationtool\.jao\.eu/core/api/data/shadowAuctionATC"
)
CORE_EXTERNAL_ATC_URL_REGEX = re.compile(
    r"https://publicationtool\.jao\.eu/core/api/data/atc"
)
TARGET_DATETIME = datetime.fromisoformat("2025-10-01T00:00:00+00:00")
CORE_EXTERNAL_TARGET_DATETIME = datetime.fromisoformat("2026-04-20T00:00:00+00:00")


def _register_shadow_auction_atc(adapter) -> None:
    payload = json.loads((BASE_MOCK_PATH / "shadow_auction_atc.json").read_text())
    adapter.register_uri(GET, SHADOW_AUCTION_ATC_URL_REGEX, json=payload)


def test_fetch_shadow_auction_atc_day_ahead_de_fr(adapter, session, snapshot):
    _register_shadow_auction_atc(adapter)

    result = fetch_shadow_auction_atc_day_ahead(
        ZoneKey("DE"),
        ZoneKey("FR"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


def test_fetch_shadow_auction_atc_day_ahead_pair_not_in_core(adapter, session):
    """Pairs without JAO border fields should return [] without raising."""
    _register_shadow_auction_atc(adapter)

    result = fetch_shadow_auction_atc_day_ahead(
        ZoneKey("DE"),
        ZoneKey("DK"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert result == []


def test_fetch_shadow_auction_atc_day_ahead_em_to_jao_zone_remap(adapter, session):
    """EM zone keys that don't match JAO's codes (e.g. IT-NO -> IT, DK-DK1 -> DK1)
    should be translated before looking up `border_XX_YY` fields."""
    remapped = {
        "data": [
            {
                "id": 1,
                "dateTimeUtc": "2025-10-01T00:00:00Z",
                "border_FR_IT": 2500,
                "border_IT_FR": 2200,
            }
        ],
        "rejected": False,
        "messages": None,
    }
    adapter.register_uri(GET, SHADOW_AUCTION_ATC_URL_REGEX, json=remapped)

    result = fetch_shadow_auction_atc_day_ahead(
        ZoneKey("FR"),
        ZoneKey("IT-NO"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert len(result) == 1
    assert result[0]["sortedZoneKeys"] == "FR->IT-NO"
    assert result[0]["capacityExport"] == 2500
    assert result[0]["capacityImport"] == 2200


def test_fetch_shadow_auction_atc_day_ahead_one_sided(adapter, session):
    """When only one direction is present in the JAO row, the event should
    still be emitted with a single populated capacity direction."""
    one_sided = {
        "data": [
            {
                "id": 1,
                "dateTimeUtc": "2025-10-01T00:00:00Z",
                "border_AT_DE": 3620,
            }
        ],
        "rejected": False,
        "messages": None,
    }
    adapter.register_uri(GET, SHADOW_AUCTION_ATC_URL_REGEX, json=one_sided)

    result = fetch_shadow_auction_atc_day_ahead(
        ZoneKey("AT"),
        ZoneKey("DE"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert len(result) == 1
    assert result[0]["capacityExport"] == 3620
    assert result[0]["capacityImport"] is None
    assert result[0]["sortedZoneKeys"] == "AT->DE"


def test_fetch_core_external_atc_day_ahead_de_dk_dk1(adapter, session, snapshot):
    """Happy path for a Core-external border that also exercises the
    DK-DK1 → DK1 zone remap. Fixture is a real 2-day, 15-min response."""
    payload = json.loads((BASE_MOCK_PATH / "core_external_atc.json").read_text())
    adapter.register_uri(GET, CORE_EXTERNAL_ATC_URL_REGEX, json=payload)

    result = fetch_core_external_atc_day_ahead(
        ZoneKey("DE"),
        ZoneKey("DK-DK1"),
        session=session,
        target_datetime=CORE_EXTERNAL_TARGET_DATETIME,
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


def test_fetch_core_external_atc_day_ahead_border_not_in_dataset(adapter, session):
    """Core-external endpoint only lists a handful of neighbors; a pair
    that isn't in the response should return [] without raising."""
    payload = json.loads((BASE_MOCK_PATH / "core_external_atc.json").read_text())
    adapter.register_uri(GET, CORE_EXTERNAL_ATC_URL_REGEX, json=payload)

    result = fetch_core_external_atc_day_ahead(
        ZoneKey("DE"),
        ZoneKey("FR"),
        session=session,
        target_datetime=CORE_EXTERNAL_TARGET_DATETIME,
    )

    assert result == []
