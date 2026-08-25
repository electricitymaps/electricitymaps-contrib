import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time
from requests_mock import ANY
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.OPENNEM import (
    _build_consumption_list,
    _build_region_net_exports,
    fetch_consumption,
    fetch_exchange,
    fetch_price,
    fetch_production,
)

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/OPENNEM")
# End of the window the flows mock covers.
EXCHANGE_TARGET_DATETIME = datetime.fromisoformat("2025-07-11T21:15:00+10:00")


@pytest.fixture(autouse=True)
def openelectricity_token_env():
    os.environ["OPENELECTRICITY_TOKEN"] = "token"


@pytest.mark.parametrize(
    "zone", ["AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-VIC", "AU-WA"]
)
def test_production(requests_mock, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_{zone}.v4.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_production(zone, session, datetime.fromisoformat("2025-03-23"))


@pytest.mark.parametrize("zone", ["AU-SA"])
def test_price(requests_mock, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_price_{zone}.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == fetch_price(
        zone, session, datetime.fromisoformat("2020-01-01")
    )


@pytest.mark.parametrize("zone", ["AU-NSW", "AU-WA"])
def test_consumption(requests_mock, session, snapshot, zone):
    mock_data = Path(base_path_to_mock, f"OPENNEM_demand_{zone}.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_consumption(
        zone, session, datetime.fromisoformat("2025-03-23T10:00:00+00:00")
    )


@freeze_time("2026-07-22 10:12:00")
def test_build_consumption_list_skips_null_future_and_malformed():
    datasets = [
        {
            "metric": "demand",
            "results": [
                {
                    "data": [
                        ["2026-07-22T20:00:00+10:00", 1000.0],  # 10:00 UTC — keep
                        ["2026-07-22T20:05:00+10:00", None],  # null — skip
                        ["bad"],  # malformed — skip
                        ["2026-07-22T20:15:00+10:00", 1100.0],  # 10:15 UTC — future
                    ]
                }
            ],
        },
        {"metric": "price", "results": [{"data": [["2026-07-22T20:00:00+10:00", 50]]}]},
    ]

    events = _build_consumption_list(
        datasets, ZoneKey("AU-NSW"), logging.getLogger("test")
    ).to_list()

    assert len(events) == 1
    assert events[0]["consumption"] == 1000.0
    assert events[0]["datetime"] == datetime.fromisoformat("2026-07-22T20:00:00+10:00")


@pytest.fixture
def flows_mock(requests_mock):
    """Every exchange is reconstructed from one region-grouped flows response."""
    mock_data = Path(base_path_to_mock, "OPENNEM_flows_NEM.json")
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(mock_data.read_text()),
    )
    return requests_mock


def test_au_nsw_au_qld_exchange(flows_mock, session, snapshot):
    assert snapshot == fetch_exchange(
        "AU-NSW", "AU-QLD", session, EXCHANGE_TARGET_DATETIME
    )


def test_au_nsw_au_vic_exchange(flows_mock, session, snapshot):
    assert snapshot == fetch_exchange(
        "AU-NSW", "AU-VIC", session, EXCHANGE_TARGET_DATETIME
    )


@pytest.mark.parametrize(
    ("zone_key1", "zone_key2", "region"),
    [("AU-SA", "AU-VIC", "SA1"), ("AU-TAS", "AU-VIC", "TAS1")],
)
def test_single_neighbour_exchange_follows_region_net_exports(
    flows_mock, session, zone_key1, zone_key2, region
):
    """
    SA and TAS each have a single neighbour, VIC, so a region exporting means a
    positive flow towards VIC, which is on the right of the arrow in both keys.
    """
    events = fetch_exchange(zone_key1, zone_key2, session, EXCHANGE_TARGET_DATETIME)

    flows = json.loads(Path(base_path_to_mock, "OPENNEM_flows_NEM.json").read_text())
    by_metric_and_datetime = {
        (dataset["metric"], datetime.fromisoformat(timestamp)): value
        for dataset in flows["data"]
        for result in dataset["results"]
        if result["columns"]["region"] == region
        for timestamp, value in result["data"]
    }

    for event in events:
        exports = by_metric_and_datetime[("flow_exports", event["datetime"])]
        imports = by_metric_and_datetime[("flow_imports", event["datetime"])]
        assert event["netFlow"] == pytest.approx(exports - imports)
        if exports > imports:
            assert event["netFlow"] > 0
        elif imports > exports:
            assert event["netFlow"] < 0

    # TAS only ever imports over the mocked window, SA does both, so neither
    # branch above is exercised by both zones - but neither is vacuous either.
    assert any(event["netFlow"] != 0 for event in events)


def test_reconstructed_flows_balance_victorias_own_series(flows_mock, session):
    """
    VIC's reported net exports must equal minus the sum of its three borders.

    This is the system-wide balance - the five regions' net exports sum to zero -
    seen through the reconstruction, so it pins the sign and weight of every
    coefficient feeding a VIC border. It cannot detect a *missing* exchange:
    region-aggregate flows carry no topology, so a new interconnector (NSW-SA,
    say) would keep the sum at zero while silently corrupting two borders.
    """
    borders = [
        fetch_exchange(zone_key1, "AU-VIC", session, EXCHANGE_TARGET_DATETIME)
        for zone_key1 in ("AU-NSW", "AU-SA", "AU-TAS")
    ]

    flows = json.loads(Path(base_path_to_mock, "OPENNEM_flows_NEM.json").read_text())
    vic = {
        (dataset["metric"], datetime.fromisoformat(timestamp)): value
        for dataset in flows["data"]
        for result in dataset["results"]
        if result["columns"]["region"] == "VIC1"
        for timestamp, value in result["data"]
    }

    assert len({len(events) for events in borders}) == 1
    for nsw_vic, sa_vic, tas_vic in zip(*borders, strict=True):
        dt = nsw_vic["datetime"]
        assert sa_vic["datetime"] == tas_vic["datetime"] == dt
        vic_net_exports = vic[("flow_exports", dt)] - vic[("flow_imports", dt)]
        assert -(
            nsw_vic["netFlow"] + sa_vic["netFlow"] + tas_vic["netFlow"]
        ) == pytest.approx(vic_net_exports, abs=1e-6)


def test_exchange_queries_region_flows_from_market_endpoint(flows_mock, session):
    fetch_exchange("AU-NSW", "AU-VIC", session, EXCHANGE_TARGET_DATETIME)

    # The flow metrics are only served by the market endpoint, the data endpoint
    # rejects them with "Unsupported metrics".
    request = flows_mock.last_request
    assert request.path == "/v4/market/network/nem"
    assert request.qs["metrics"] == ["flow_imports", "flow_exports"]
    assert request.qs["primary_grouping"] == ["network_region"]
    # Reconstructing an exchange needs several regions, so no region filter is
    # sent, and one response covers every term of the sum on aligned timestamps.
    assert "network_region" not in request.qs
    assert len(flows_mock.request_history) == 1


def test_exchange_raises_when_a_region_is_missing(requests_mock, session):
    requests_mock.register_uri(
        ANY,
        ANY,
        json={
            "data": [
                {
                    "metric": metric,
                    "interval": "5m",
                    "results": [
                        {
                            "columns": {"region": "NSW1"},
                            "data": [["2025-07-10T21:15:00+10:00", 100.0]],
                        }
                    ],
                }
                for metric in ("flow_imports", "flow_exports")
            ]
        },
    )

    # AU-NSW->AU-VIC also needs QLD1, to subtract the NSW-QLD flows.
    with pytest.raises(ParserException, match="QLD1"):
        fetch_exchange("AU-NSW", "AU-VIC", session, EXCHANGE_TARGET_DATETIME)


def test_build_region_net_exports_pairs_imports_with_exports():
    datasets = [
        {
            "metric": "flow_imports",
            "results": [
                {
                    "columns": {"region": "NSW1"},
                    "data": [
                        ["2025-07-10T21:15:00+10:00", 100.0],
                        ["2025-07-10T21:20:00+10:00", 200.0],
                        ["2025-07-10T21:25:00+10:00", 300.0],  # no export — skip
                        ["2025-07-10T21:30:00+10:00", None],  # null — skip
                        ["bad"],  # malformed — skip
                    ],
                }
            ],
        },
        {
            "metric": "flow_exports",
            "results": [
                {
                    "columns": {"region": "NSW1"},
                    "data": [
                        ["2025-07-10T21:15:00+10:00", 0.0],
                        ["2025-07-10T21:20:00+10:00", 250.0],
                        ["2025-07-10T21:30:00+10:00", 400.0],  # import was null
                        ["2025-07-10T21:35:00+10:00", 500.0],  # no import — skip
                    ],
                }
            ],
        },
        {
            "metric": "price",  # not a flow metric — ignored
            "results": [
                {
                    "columns": {"region": "NSW1"},
                    "data": [["2025-07-10T21:15:00+10:00", 50.0]],
                }
            ],
        },
    ]

    assert _build_region_net_exports(datasets) == {
        "NSW1": {
            datetime.fromisoformat("2025-07-10T21:15:00+10:00"): -100.0,
            datetime.fromisoformat("2025-07-10T21:20:00+10:00"): 50.0,
        }
    }
