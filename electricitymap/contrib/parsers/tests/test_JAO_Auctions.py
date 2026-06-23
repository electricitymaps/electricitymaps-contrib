import json
import os
import re
from datetime import datetime
from pathlib import Path

from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.parsers.JAO_Auctions import fetch_auction_atc_day_ahead

os.environ["JAO_AUCTION_API_KEY"] = "dummy"

BASE_MOCK_PATH = Path("electricitymap/contrib/parsers/tests/mocks/JAO_Auctions")
ATC_DAY_AHEAD_AUCTION_URL_REGEX = re.compile(r"https://api.jao.eu/OWSMP/getauctions")
TARGET_DATETIME = datetime.fromisoformat("2026-06-01T00:00:00+00:00")


def _corridor_callback(base_path: Path):
    """Return a callback that serves per-corridor JSON files from base_path.

    Files are looked up as {base_path}/{corridor}.json so each corridor can
    carry distinct capacity values — the test then validates the parser sums
    them correctly. Unknown corridors return [] (no data for that window).
    """

    def callback(request, _):
        corridor = request.qs.get("corridor", [""])[0]
        mock_file = base_path / f"{corridor}.json"
        if mock_file.exists():
            return json.loads(mock_file.read_text())
        return []

    return callback


def _single_hour_callback(capacity_by_corridor: dict):
    """Return a callback that serves a one-hour response keyed by corridor name.

    Useful for inline tests: pass {corridor: offeredCapacity} and unknown
    corridors return [] (simulating no auction data for that direction).
    """

    def callback(request, _):
        corridor = request.qs.get("corridor", [""])[0]
        capacity = capacity_by_corridor.get(corridor)
        if capacity is None:
            return []
        return [
            {
                "marketPeriodStart": "2026-06-01T00:00:00+00:00",
                "results": [{"productHour": "00-01", "offeredCapacity": capacity}],
            }
        ]

    return callback


def _register_auction_atc(requests_mock) -> None:
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        json=_corridor_callback(BASE_MOCK_PATH),
    )


def test_fetch_auction_atc_day_ahead_fr_gb(requests_mock, session, snapshot):
    _register_auction_atc(requests_mock)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("FR"),
        ZoneKey("GB"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


def test_fetch_auction_atc_day_ahead_pair_not_in_auction(requests_mock, session):
    """Borders not in EM_ZONE_TO_JAO_PREFIX use an empty prefix (corridors DE-DK /
    DK-DE). When the API returns no data for those corridors, result is []."""
    _register_auction_atc(requests_mock)

    result = fetch_auction_atc_day_ahead(
        ZoneKey("DE"),
        ZoneKey("DK"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert result == []


def test_fetch_auction_atc_day_ahead_em_to_jao_zone_remap(requests_mock, session):
    """DK-DK1 must be remapped to D1 in corridor names.
    Export corridor is VKL-D1-GB, import corridor is VKL-GB-D1."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        json=_single_hour_callback({"vkl-d1-gb": 2500, "vkl-gb-d1": 2200}),
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("DK-DK1"),
        ZoneKey("GB"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert len(result) == 1
    assert result[0]["sortedZoneKeys"] == "DK-DK1->GB"
    assert result[0]["capacityExport"] == 2500
    assert result[0]["capacityImport"] == 2200


def test_fetch_auction_atc_day_ahead_one_sided(requests_mock, session):
    """When only the export corridor (NLL-BE-GB) has data and the import
    corridor (NLL-GB-BE) returns [], capacityImport should be None."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        json=_single_hour_callback({"nll-be-gb": 3620}),
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("BE"),
        ZoneKey("GB"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert len(result) == 1
    assert result[0]["sortedZoneKeys"] == "BE->GB"
    assert result[0]["capacityExport"] == 3620
    assert result[0]["capacityImport"] is None
