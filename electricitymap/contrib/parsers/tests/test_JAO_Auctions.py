import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers.JAO_Auctions import fetch_auction_atc_day_ahead
from electricitymap.contrib.types import AtcType

os.environ["JAO_AUCTION_API_KEY"] = "dummy"

BASE_MOCK_PATH = Path("electricitymap/contrib/parsers/tests/mocks/JAO_Auctions")
ATC_DAY_AHEAD_AUCTION_URL_REGEX = re.compile(r"https://api.jao.eu/OWSMP/getauctions")
TARGET_DATETIME = datetime.fromisoformat("2026-06-01T00:00:00+00:00")


def test_fetch_auction_atc_day_ahead_fr_gb(requests_mock, session, snapshot):
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {"json": json.loads((BASE_MOCK_PATH / "if1-fr-gb.json").read_text())},
            {"json": json.loads((BASE_MOCK_PATH / "if1-gb-fr.json").read_text())},
            {"json": json.loads((BASE_MOCK_PATH / "if2-fr-gb.json").read_text())},
            {"json": json.loads((BASE_MOCK_PATH / "if2-gb-fr.json").read_text())},
            {"json": json.loads((BASE_MOCK_PATH / "el1-fr-gb.json").read_text())},
            {"json": json.loads((BASE_MOCK_PATH / "el1-gb-fr.json").read_text())},
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


def test_fetch_auction_atc_day_ahead_pair_not_in_auction(requests_mock, session):
    """Borders not in EM_ZONE_TO_JAO_PREFIX use an empty prefix (corridors DE-DK /
    DK-DE). When the API returns no data for those corridors, result is []."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        json=[],
    )

    result = fetch_auction_atc_day_ahead(
        ZoneKey("DE"),
        ZoneKey("DK"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    corridors = [r.qs["corridor"][0] for r in requests_mock.request_history]
    assert corridors == ["de-dk", "dk-de"]
    assert result == []


def test_fetch_auction_atc_day_ahead_em_to_jao_zone_remap(requests_mock, session):
    """DK-DK1 must be remapped to D1 in corridor names.
    Export corridor is VKL-D1-GB, import corridor is VKL-GB-D1."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {
                "json": [
                    {
                        "marketPeriodStart": "2026-06-01T00:00:00+00:00",
                        "results": [{"productHour": "00-01", "offeredCapacity": 2500}],
                    }
                ]
            },
            {
                "json": [
                    {
                        "marketPeriodStart": "2026-06-01T00:00:00+00:00",
                        "results": [{"productHour": "00-01", "offeredCapacity": 2200}],
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
            "datetime": datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": None,
            "sortedZoneKeys": "DK-DK1->GB",
            "capacityExport": 2500.0,
            "capacityImport": 2200.0,
            "atcType": AtcType.COORDINATED_NTC,
            "source": "jao.eu",
            "sourceType": EventSourceType.published,
        }
    ]


def test_fetch_auction_atc_day_ahead_one_sided_export(requests_mock, session):
    """When only the export corridor (CH-DE) has data and the import
    corridor (DE-CH) returns [], capacityImport should be None."""
    requests_mock.register_uri(
        GET,
        ATC_DAY_AHEAD_AUCTION_URL_REGEX,
        response_list=[
            {
                "json": [
                    {
                        "marketPeriodStart": "2026-06-01T00:00:00+00:00",
                        "results": [{"productHour": "00-01", "offeredCapacity": 3620}],
                    }
                ]
            },
            {"json": []},
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
            "datetime": datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": None,
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
            {"json": []},  # vkl-d1-gb (export) — no data
            {
                "json": [
                    {
                        "marketPeriodStart": "2026-06-01T00:00:00+00:00",
                        "results": [{"productHour": "00-01", "offeredCapacity": 1800}],
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
            "datetime": datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
            "end_datetime": None,
            "sortedZoneKeys": "DK-DK1->GB",
            "capacityExport": None,
            "capacityImport": 1800.0,
            "atcType": AtcType.COORDINATED_NTC,
            "source": "jao.eu",
            "sourceType": EventSourceType.published,
        }
    ]
