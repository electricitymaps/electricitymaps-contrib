import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from requests_mock import ANY, GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.lib.models.event_lists import ExchangeCapacityForecastList
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers import ENTSOE
from electricitymap.contrib.parsers.ENTSOE import (
    _get_datetime_value_from_timeseries,
    _merge_exchange_capacity_forecasts,
    fetch_production,
    parse_exchange_capacity_forecast,
    zulu_to_utc,
)
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/ENTSOE")


@pytest.fixture(autouse=True)
def entsoe_token_env():
    os.environ["ENTSOE_TOKEN"] = "token"


def test_fetch_consumption(adapter, session, snapshot):
    data = base_path_to_mock / "DK-DK1_consumption.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_consumption(ZoneKey("DK-DK1"), session)


def test_fetch_consumption_forecast(adapter, session, snapshot):
    data = base_path_to_mock / "DK-DK2_consumption_forecast.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_consumption_forecast(ZoneKey("DK-DK2"), session)


def test_fetch_consumption_aggregated_zone(monkeypatch):
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    called_domains: list[str] = []

    def fake_query_consumption(in_domain, session, target_datetime=None):
        called_domains.append(in_domain)
        if in_domain == ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-CA"]:
            return "raw-it-ca"
        if in_domain == ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-SO"]:
            return "raw-it-so"
        raise AssertionError(f"Unexpected domain {in_domain}")

    def fake_parse_scalar(raw_xml, only_outBiddingZone_Domain=True):
        if raw_xml == "raw-it-ca":
            return [(dt, 70.0)]
        if raw_xml == "raw-it-so":
            return [(dt, 30.0)]
        return None

    monkeypatch.setattr(ENTSOE, "query_consumption", fake_query_consumption)
    monkeypatch.setattr(ENTSOE, "parse_scalar", fake_parse_scalar)

    result = ENTSOE.fetch_consumption(ZoneKey("IT-SO"), session=None)

    assert called_domains == [
        ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-CA"],
        ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-SO"],
    ]
    assert result == [
        {
            "datetime": dt,
            "zoneKey": ZoneKey("IT-SO"),
            "consumption": 100.0,
            "source": ENTSOE.SOURCE,
            "sourceType": EventSourceType.measured,
        }
    ]


def test_fetch_generation_forecast(adapter, session, snapshot):
    data = base_path_to_mock / "SE-SE3_generation_forecast.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_generation_forecast(ZoneKey("SE-SE3"), session)


def test_fetch_generation_forecast_aggregated_zone(monkeypatch):
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    called_domains: list[str] = []

    def fake_query_generation_forecast(in_domain, session, target_datetime=None):
        called_domains.append(in_domain)
        if in_domain == ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-CA"]:
            return "raw-it-ca"
        if in_domain == ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-SO"]:
            return "raw-it-so"
        raise AssertionError(f"Unexpected domain {in_domain}")

    def fake_parse_scalar(raw_xml, only_inBiddingZone_Domain=True):
        if raw_xml == "raw-it-ca":
            return [(dt, 120.0)]
        if raw_xml == "raw-it-so":
            return [(dt, 80.0)]
        return None

    monkeypatch.setattr(
        ENTSOE, "query_generation_forecast", fake_query_generation_forecast
    )
    monkeypatch.setattr(ENTSOE, "parse_scalar", fake_parse_scalar)

    result = ENTSOE.fetch_generation_forecast(ZoneKey("IT-SO"), session=None)

    assert called_domains == [
        ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-CA"],
        ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IT-SO"],
    ]
    assert result == [
        {
            "datetime": dt,
            "zoneKey": ZoneKey("IT-SO"),
            "value": 200.0,
            "source": ENTSOE.SOURCE,
            "sourceType": EventSourceType.forecasted,
        }
    ]


def test_fetch_prices_day_ahead(adapter, session, snapshot):
    data = base_path_to_mock / "ES_day_ahead_price.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_price(ZoneKey("ES"), session)


def test_fetch_prices_intraday(adapter, session, snapshot):
    data = base_path_to_mock / "ES_intraday_price.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_price_intraday(ZoneKey("ES"), session)


def test_fetch_prices_integrated_zone(adapter, session, snapshot):
    data = base_path_to_mock / "FR_prices.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )
    assert snapshot == ENTSOE.fetch_price(ZoneKey("DK-BHM"), session)


def test_fetch_with_negative_values(adapter, session, snapshot):
    data = base_path_to_mock / "NO-NO5_production-negatives.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )
    logger = logging.Logger("test")
    assert snapshot == ENTSOE.fetch_production(
        ZoneKey("NO-NO5"), session, logger=logger
    )


@pytest.mark.parametrize("zone", ["FI", "LU", "NO-NO5", "SE-SE4"])
def test_production_with_snapshot(adapter, session, snapshot, zone):
    raw_data = base_path_to_mock / f"{zone}_production.xml"
    adapter.register_uri(
        GET,
        ANY,
        content=raw_data.read_bytes(),
    )
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == ENTSOE.fetch_production(ZoneKey(zone), session)


def test_fetch_exchange(adapter, session, snapshot):
    imports = base_path_to_mock / "DK-DK1_GB_exchange_imports.xml"
    exports = base_path_to_mock / "DK-DK1_GB_exchange_exports.xml"

    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10YDK-1--------W&out_Domain=10YGB----------A",
        content=imports.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10YGB----------A&out_Domain=10YDK-1--------W",
        content=exports.read_bytes(),
    )
    assert snapshot == ENTSOE.fetch_exchange(
        zone_key1=ZoneKey("DK-DK1"), zone_key2=ZoneKey("GB"), session=session
    )


def test_fetch_exchange_with_aggregated_exchanges(adapter, session, snapshot):
    imports_AC = base_path_to_mock / "FR-COR_IT-SAR_AC_exchange_imports.xml"
    exports_AC = base_path_to_mock / "FR-COR_IT-SAR_AC_exchange_exports.xml"
    imports_DC = base_path_to_mock / "FR-COR_IT-SAR_DC_exchange_imports.xml"
    exports_DC = base_path_to_mock / "FR-COR_IT-SAR_DC_exchange_exports.xml"

    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A885&out_Domain=10Y1001A1001A74G",
        content=imports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A885",
        content=exports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A893&out_Domain=10Y1001A1001A74G",
        content=imports_DC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A11&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A893",
        content=exports_DC.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange(
        zone_key1=ZoneKey("FR-COR"),
        zone_key2=ZoneKey("IT-SAR"),
        session=session,
    )


def test_fetch_exchange_forecast(adapter, session, snapshot):
    imports = base_path_to_mock / "DK-DK2_SE-SE4_exchange_forecast_imports.xml"
    exports = base_path_to_mock / "DK-DK2_SE-SE4_exchange_forecast_exports.xml"

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YDK-2--------M&out_Domain=10Y1001A1001A47J",
        content=imports.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A47J&out_Domain=10YDK-2--------M",
        content=exports.read_bytes(),
    )
    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("DK-DK2"),
        zone_key2=ZoneKey("SE-SE4"),
        session=session,
    )


def test_fetch_exchange_forecast_15_min(adapter, session, snapshot):
    imports = base_path_to_mock / "BE_NL_exchange_forecast_imports.xml"
    exports = base_path_to_mock / "BE_NL_exchange_forecast_exports.xml"

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YBE----------2&out_Domain=10YNL----------L",
        content=imports.read_bytes(),
    )

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YNL----------L&out_Domain=10YBE----------2",
        content=exports.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("BE"), zone_key2=ZoneKey("NL"), session=session
    )


def test_fetch_exchange_forecast_with_longer_day_ahead_than_total(
    adapter, session, snapshot
):
    imports = base_path_to_mock / "EE_FI_exchange_forecast_imports.xml"
    exports = base_path_to_mock / "EE_FI_exchange_forecast_exports.xml"

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A39I&out_Domain=10YFI-1--------U",
        content=imports.read_bytes(),
    )

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10YFI-1--------U&out_Domain=10Y1001A1001A39I",
        content=exports.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("EE"), zone_key2=ZoneKey("FI"), session=session
    )


def test_fetch_exchange_forecast_with_aggregated_exchanges(adapter, session, snapshot):
    imports_AC = base_path_to_mock / "FR-COR_IT-SAR_AC_exchange_forecast_imports.xml"
    exports_AC = base_path_to_mock / "FR-COR_IT-SAR_AC_exchange_forecast_exports.xml"
    imports_DC = base_path_to_mock / "FR-COR_IT-SAR_DC_exchange_forecast_imports.xml"
    exports_DC = base_path_to_mock / "FR-COR_IT-SAR_DC_exchange_forecast_exports.xml"

    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A885&out_Domain=10Y1001A1001A74G",
        content=imports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A885",
        content=exports_AC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A893&out_Domain=10Y1001A1001A74G",
        content=imports_DC.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A09&in_Domain=10Y1001A1001A74G&out_Domain=10Y1001A1001A893",
        content=exports_DC.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_forecast(
        zone_key1=ZoneKey("FR-COR"),
        zone_key2=ZoneKey("IT-SAR"),
        session=session,
    )


def test_wind_and_solar_forecasts(adapter, session, snapshot):
    day_ahead = base_path_to_mock / "wind_solar_forecast_FI_DAY_AHEAD.xml"
    intraday = base_path_to_mock / "wind_solar_forecast_FI_INTRADAY.xml"
    current = base_path_to_mock / "wind_solar_forecast_FI_CURRENT.xml"

    adapter.register_uri(
        GET,
        "?documentType=A69&processType=A01",
        content=day_ahead.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A69&processType=A40",
        content=intraday.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A69&processType=A18",
        content=current.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_wind_solar_forecasts(ZoneKey("FI"), session)


def test_fetch_uses_normal_url(adapter, session):
    os.environ["ENTSOE_TOKEN"] = "proxy"
    with open(
        "electricitymap/contrib/parsers/tests/mocks/ENTSOE/FR_prices.xml", "rb"
    ) as price_fr_data:
        adapter.register_uri(
            GET,
            ENTSOE.ENTSOE_URL,
            content=price_fr_data.read(),
        )
    ENTSOE.fetch_price(ZoneKey("DE"), session)


def test_refetch_frequency():
    func = fetch_production

    assert func.__name__ == "fetch_production"


# Below are tests for the time series parsing functions.


def _make_soup(xml: str):
    return BeautifulSoup(xml, "html.parser")


def test_a01_timeseries_parsing_production_and_consumption():
    """A01 curve: simple per-position points. Check datetimes and sign handling for production_parsing."""
    xml = """
    <timeseries>
      <curvetype>A01</curvetype>
      <inbiddingzone_domain.mrid>TEST</inbiddingzone_domain.mrid>
      <period>
        <start>2023-01-01T00:00:00Z</start>
        <end>2023-01-01T02:00:00Z</end>
        <resolution>PT60M</resolution>
        <point>
          <position>1</position>
          <quantity>10</quantity>
        </point>
        <point>
          <position>2</position>
          <quantity>20</quantity>
        </point>
      </period>
    </timeseries>
    """

    soup = _make_soup(xml)
    ts = soup.find("timeseries")

    results = list(
        _get_datetime_value_from_timeseries(ts, "quantity", production_parsing=True)
    )

    assert len(results) == 2

    dt0_expected = datetime.fromisoformat(zulu_to_utc("2023-01-01T00:00:00Z"))
    dt1_expected = dt0_expected + timedelta(hours=1)

    assert results[0][0] == dt0_expected and results[0][1] == 10.0
    assert results[1][0] == dt1_expected and results[1][1] == 20.0

    # Now test consumption (no inbidding tag) becomes negative when production_parsing=True
    xml_consumption = xml.replace(
        "<inbiddingzone_domain.mrid>TEST</inbiddingzone_domain.mrid>", ""
    )
    soup2 = _make_soup(xml_consumption)
    ts2 = soup2.find("timeseries")
    results2 = list(
        _get_datetime_value_from_timeseries(ts2, "quantity", production_parsing=True)
    )
    assert results2[0][1] == -10.0
    assert results2[1][1] == -20.0


def test_a03_curve_compression_expands_segments_correctly():
    """A03 curve: compressed segments. Frame start positions indicate start of a constant segment up to next frame start."""
    # We'll create two frames: frame at position 1 value 10, frame at position 3 value 20
    # With resolution PT60M and start 2023-01-01T00:00:00Z this should yield:
    # pos1 -> 00:00 value 10
    # pos2 -> 01:00 value 10 (filled from frame 1)
    # pos3 -> 02:00 value 20 (last frame)
    xml = """
    <timeseries>
      <curvetype>A03</curvetype>
      <period>
        <start>2023-01-01T00:00:00Z</start>
        <end>2023-01-01T03:00:00Z</end>
        <resolution>PT60M</resolution>
        <point>
          <position>1</position>
          <quantity>10</quantity>
        </point>
        <point>
          <position>3</position>
          <quantity>20</quantity>
        </point>
      </period>
    </timeseries>
    """

    soup = _make_soup(xml)
    ts = soup.find("timeseries")
    results = list(
        _get_datetime_value_from_timeseries(ts, "quantity", production_parsing=False)
    )

    # Expect three datapoints as explained above
    assert len(results) == 3

    dt0 = datetime.fromisoformat(zulu_to_utc("2023-01-01T00:00:00Z"))
    assert results[0] == (dt0, 10.0)
    assert results[1] == (dt0 + timedelta(hours=1), 10.0)
    assert results[2] == (dt0 + timedelta(hours=2), 20.0)


def test_a03_curve_compression_expands_1_datapoint_correctly():
    """A03 curve: compressed segments. Frame start positions indicate start of a constant segment up to next frame start."""
    # We'll create two frames: frame at position 1 value 10, frame at position 3 value 20
    # With resolution PT60M and start 2023-01-01T00:00:00Z this should yield:
    # pos1 -> 00:00 value 10
    # pos2 -> 01:00 value 10 (filled from frame 1)
    # pos3 -> 02:00 value 20 (last frame)
    xml = """
    <timeseries>
      <curvetype>A03</curvetype>
      <period>
        <start>2023-01-01T00:00:00Z</start>
        <end>2023-01-01T03:00:00Z</end>
        <resolution>PT60M</resolution>
        <point>
          <position>1</position>
          <quantity>10</quantity>
        </point>
      </period>
    </timeseries>
    """

    soup = _make_soup(xml)
    ts = soup.find("timeseries")
    results = list(
        _get_datetime_value_from_timeseries(ts, "quantity", production_parsing=False)
    )

    # Expect three datapoints as explained above
    assert len(results) == 3

    dt0 = datetime.fromisoformat(zulu_to_utc("2023-01-01T00:00:00Z"))
    assert results[0] == (dt0, 10.0)
    assert results[1] == (dt0 + timedelta(hours=1), 10.0)
    assert results[2] == (dt0 + timedelta(hours=2), 10.0)


@pytest.mark.parametrize(
    "fixture",
    [
        "fake_time_series.xml",
        "fake_time_series_all_0.xml",
    ],
)
def test_a03_curve_decompression(fixture, snapshot):
    """A03 curve: compressed segments. Full example from ENTSOE with production data."""
    soup = _make_soup(Path(base_path_to_mock, fixture).read_text())
    ts = soup.find("timeseries")
    results = list(
        _get_datetime_value_from_timeseries(ts, "quantity", production_parsing=True)
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == results


# ─── parse_exchange_capacity_forecast ────────────────────────────────────────


def test_parse_exchange_capacity_forecast_week_ahead_export_direction():
    """export direction populates capacityExport, leaves capacityImport None."""
    xml = (
        base_path_to_mock / "DK-DK1_DK-DK2_capacity_week_ahead_export.xml"
    ).read_text()
    logger = logging.getLogger("test")
    result = parse_exchange_capacity_forecast(
        xml, ZoneKey("DK-DK1->DK-DK2"), logger, direction="export"
    )
    events = result.events
    assert len(events) == 40
    dt0 = datetime(2026, 2, 16, 23, 0, tzinfo=timezone.utc)
    assert events[0].datetime == dt0
    assert events[0].capacityExport == 600.0
    assert events[0].capacityImport is None
    assert events[1].datetime == dt0 + timedelta(days=1)
    assert events[1].capacityExport == 600.0
    assert events[1].capacityImport is None
    assert events[0].sourceType == EventSourceType.forecasted


def test_parse_exchange_capacity_forecast_week_ahead_import_direction():
    """Import direction populates capacityImport, leaves capacityExport None."""
    xml = (
        base_path_to_mock / "DK-DK1_DK-DK2_capacity_week_ahead_import.xml"
    ).read_text()
    logger = logging.getLogger("test")
    result = parse_exchange_capacity_forecast(
        xml, ZoneKey("DK-DK1->DK-DK2"), logger, direction="import"
    )
    events = result.events
    assert len(events) == 40
    assert events[0].capacityImport == 450.0
    assert events[0].capacityExport is None
    assert events[1].capacityImport == 450.0
    assert events[1].capacityExport is None


def test_parse_exchange_capacity_forecast_day_ahead_export_direction():
    """export direction populates capacityExport, leaves capacityImport None."""
    xml = (base_path_to_mock / "ES_FR_capacity_day_ahead_export.xml").read_text()
    logger = logging.getLogger("test")
    result = parse_exchange_capacity_forecast(
        xml, ZoneKey("ES->FR"), logger, direction="export"
    )
    events = result.events
    assert len(events) == 41
    dt0 = datetime(2026, 3, 19, 6, 0, tzinfo=timezone.utc)
    assert events[0].datetime == dt0
    assert events[0].capacityExport == 3006.0
    assert events[0].capacityImport is None
    assert events[1].datetime == dt0 + timedelta(hours=1)
    assert events[1].capacityExport == 3006.0
    assert events[1].capacityImport is None
    assert events[4].capacityExport == 2914.0
    assert events[-1].capacityExport == 3607.0
    assert events[0].sourceType == EventSourceType.forecasted


def test_parse_exchange_capacity_forecast_month_ahead_import_direction():
    """import direction populates capacityImport, leaves capacityExport None."""
    xml = (base_path_to_mock / "ES_FR_capacity_month_ahead_import.xml").read_text()
    logger = logging.getLogger("test")
    result = parse_exchange_capacity_forecast(
        xml, ZoneKey("ES->FR"), logger, direction="import"
    )
    events = result.events
    assert len(events) == 62
    dt0 = datetime(2026, 3, 16, 23, 0, tzinfo=timezone.utc)
    assert events[0].datetime == dt0
    assert events[0].capacityExport is None
    assert events[0].capacityImport == 2150.0
    assert events[1].datetime == dt0 + timedelta(days=1)
    assert events[1].capacityExport is None
    assert events[1].capacityImport == 2150.0
    assert events[2].capacityImport == 2400.0
    assert events[0].sourceType == EventSourceType.forecasted


def test_parse_exchange_capacity_forecast_empty_xml():
    """Empty XML (no TimeSeries) returns an empty list."""
    logger = logging.getLogger("test")
    result = parse_exchange_capacity_forecast(
        "<root></root>", ZoneKey("AT->DE"), logger, direction="export"
    )
    assert result.events == []


def test_parse_exchange_capacity_forecast_multiple_timeseries():
    """Multiple TimeSeries blocks are all parsed."""
    xml = """
    <root>
      <TimeSeries>
        <curveType>A03</curveType>
        <Period>
          <start>2023-01-01T00:00Z</start>
          <end>2023-01-01T01:00Z</end>
          <resolution>PT60M</resolution>
          <Point><position>1</position><quantity>100</quantity></Point>
        </Period>
      </TimeSeries>
      <TimeSeries>
        <curveType>A03</curveType>
        <Period>
          <start>2023-01-01T01:00Z</start>
          <end>2023-01-01T02:00Z</end>
          <resolution>PT60M</resolution>
          <Point><position>1</position><quantity>200</quantity></Point>
        </Period>
      </TimeSeries>
    </root>
    """
    logger = logging.getLogger("test")
    result = parse_exchange_capacity_forecast(
        xml, ZoneKey("AT->DE"), logger, direction="export"
    )
    assert len(result.events) == 2
    assert result.events[0].capacityExport == 100.0
    assert result.events[1].capacityExport == 200.0


# ─── _merge_exchange_capacity_forecasts ──────────────────────────────────────


def _make_capacity_list(
    zone_key: ZoneKey,
    datetimes: list[datetime],
    forward: list[float | None],
    reverse: list[float | None],
) -> ExchangeCapacityForecastList:
    logger = logging.getLogger("test")
    lst = ExchangeCapacityForecastList(logger)
    for dt, fwd, rev in zip(datetimes, forward, reverse, strict=True):
        lst.append(
            zoneKey=zone_key,
            datetime=dt,
            source="entsoe.eu",
            capacityExport=fwd,
            capacityImport=rev,
        )
    return lst


def test_merge_exchange_capacity_forecasts_both_directions():
    """Both directions present for same datetimes → merged event has both capacities."""
    logger = logging.getLogger("test")
    dt1 = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc)
    zone_key = ZoneKey("AT->DE")

    forward = _make_capacity_list(zone_key, [dt1, dt2], [600.0, 500.0], [None, None])
    reverse = _make_capacity_list(zone_key, [dt1, dt2], [None, None], [400.0, 350.0])

    merged = _merge_exchange_capacity_forecasts(forward, reverse, logger)
    events = merged.events

    assert len(events) == 2
    assert events[0].datetime == dt1
    assert events[0].capacityExport == 600.0
    assert events[0].capacityImport == 400.0
    assert events[1].datetime == dt2
    assert events[1].capacityExport == 500.0
    assert events[1].capacityImport == 350.0


def test_merge_exchange_capacity_forecasts_only_forward():
    """Only forward data → merged events have capacityImport=None."""
    logger = logging.getLogger("test")
    dt = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    zone_key = ZoneKey("AT->DE")

    forward = _make_capacity_list(zone_key, [dt], [600.0], [None])
    reverse = ExchangeCapacityForecastList(logger)

    merged = _merge_exchange_capacity_forecasts(forward, reverse, logger)
    events = merged.events

    assert len(events) == 1
    assert events[0].capacityExport == 600.0
    assert events[0].capacityImport is None


def test_merge_exchange_capacity_forecasts_only_reverse():
    """Only reverse data → merged events have capacityExport=None."""
    logger = logging.getLogger("test")
    dt = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    zone_key = ZoneKey("AT->DE")

    forward = ExchangeCapacityForecastList(logger)
    reverse = _make_capacity_list(zone_key, [dt], [None], [400.0])

    merged = _merge_exchange_capacity_forecasts(forward, reverse, logger)
    events = merged.events

    assert len(events) == 1
    assert events[0].capacityExport is None
    assert events[0].capacityImport == 400.0


def test_merge_exchange_capacity_forecasts_non_overlapping_datetimes():
    """Non-overlapping datetime sets → all datetimes present in merged result."""
    logger = logging.getLogger("test")
    dt1 = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc)
    zone_key = ZoneKey("AT->DE")

    forward = _make_capacity_list(zone_key, [dt1], [600.0], [None])
    reverse = _make_capacity_list(zone_key, [dt2], [None], [400.0])

    merged = _merge_exchange_capacity_forecasts(forward, reverse, logger)
    events = merged.events

    assert len(events) == 2
    assert events[0].datetime == dt1
    assert events[0].capacityExport == 600.0
    assert events[0].capacityImport is None
    assert events[1].datetime == dt2
    assert events[1].capacityExport is None
    assert events[1].capacityImport == 400.0


def test_merge_exchange_capacity_forecasts_prefers_forward_zone_key():
    """When both directions exist, zone key and source are taken from the forward event."""
    logger = logging.getLogger("test")
    dt = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
    zone_key = ZoneKey("AT->DE")

    forward = _make_capacity_list(zone_key, [dt], [600.0], [None])
    reverse = _make_capacity_list(zone_key, [dt], [None], [400.0])

    merged = _merge_exchange_capacity_forecasts(forward, reverse, logger)
    assert merged.events[0].zoneKey == zone_key
    assert merged.events[0].source == "entsoe.eu"


def test_fetch_exchange_capacity_forecasts_day_ahead(adapter, session, snapshot):
    export_data = base_path_to_mock / "ES_FR_capacity_day_ahead_export.xml"
    import_data = base_path_to_mock / "ES_FR_capacity_day_ahead_import.xml"

    adapter.register_uri(
        GET,
        "?documentType=A61&Contract_MarketAgreement.Type=A01&in_Domain=10YES-REE------0&out_Domain=10YFR-RTE------C",
        content=export_data.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A61&Contract_MarketAgreement.Type=A01&in_Domain=10YFR-RTE------C&out_Domain=10YES-REE------0",
        content=import_data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_capacity_forecasts_day_ahead(
        zone_key1=ZoneKey("ES"),
        zone_key2=ZoneKey("FR"),
        session=session,
    )


def test_fetch_exchange_capacity_forecasts_week_ahead(adapter, session, snapshot):
    export_data = base_path_to_mock / "DK-DK1_DK-DK2_capacity_week_ahead_export.xml"
    import_data = base_path_to_mock / "DK-DK1_DK-DK2_capacity_week_ahead_import.xml"

    adapter.register_uri(
        GET,
        "?documentType=A61&Contract_MarketAgreement.Type=A02&in_Domain=10YDK-1--------W&out_Domain=10YDK-2--------M",
        content=export_data.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A61&Contract_MarketAgreement.Type=A02&in_Domain=10YDK-2--------M&out_Domain=10YDK-1--------W",
        content=import_data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_capacity_forecasts_week_ahead(
        zone_key1=ZoneKey("DK-DK1"),
        zone_key2=ZoneKey("DK-DK2"),
        session=session,
    )


def test_fetch_exchange_capacity_forecasts_month_ahead(adapter, session, snapshot):
    export_data = base_path_to_mock / "ES_FR_capacity_month_ahead_export.xml"
    import_data = base_path_to_mock / "ES_FR_capacity_month_ahead_import.xml"

    adapter.register_uri(
        GET,
        "?documentType=A61&Contract_MarketAgreement.Type=A03&in_Domain=10YES-REE------0&out_Domain=10YFR-RTE------C",
        content=export_data.read_bytes(),
    )
    adapter.register_uri(
        GET,
        "?documentType=A61&Contract_MarketAgreement.Type=A03&in_Domain=10YFR-RTE------C&out_Domain=10YES-REE------0",
        content=import_data.read_bytes(),
    )

    assert snapshot == ENTSOE.fetch_exchange_capacity_forecasts_month_ahead(
        zone_key1=ZoneKey("ES"),
        zone_key2=ZoneKey("FR"),
        session=session,
    )
