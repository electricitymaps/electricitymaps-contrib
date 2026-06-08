"""Tests for the JP area supply-demand CSV parser (Phase 1).

Covers all 10 zones with real fixture data:
  01 JP-HKD (Hokkaido)  — 22-col, Shift-JIS, zero-padded dates
  02 JP-TH  (Tohoku)    — 22-col, Shift-JIS, realtime file naming
  03 JP-TK  (Tokyo)     — 20-col, UTF-8
  04 JP-CB  (Chubu)     — 20-col, Shift-JIS, March 2026 data
  05 JP-HR  (Hokuriku)  — 22-col, Shift-JIS
  06 JP-KN  (Kansai)    — 20-col, Shift-JIS, full-width parens
  07 JP-CG  (Chugoku)   — 22-col, Shift-JIS
  08 JP-SK  (Shikoku)   — 20-col, Shift-JIS, empty cells (NaN)
  09 JP-KY  (Kyushu)    — 20-col, Shift-JIS, quoted, compact date, full-width LNG
  10 JP-ON  (Okinawa)   — 22-col, Shift-JIS
"""

from datetime import datetime
from io import BytesIO
from logging import getLogger
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import pytest

from electricitymap.contrib.parsers.JP import (
    _AREA_COLUMN_MAP,
    _AREA_CSV_CONFIGS,
    _AREA_CSV_START_DATES,
    _LEGACY_AREA_CONFIGS,
    _LEGACY_AREA_START_DATES,
    _build_legacy_datetime,
    _df_to_production_breakdown_list,
    _fetch_area_csv_content,
    _fetch_production_legacy_area_csv,
    _fiscal_quarter,
    _fiscal_year,
    _hr_legacy_url,
    _legacy_df_to_breakdown,
    _legacy_value_to_float,
    _parse_area_datetime,
    _read_area_csv,
    _read_legacy_area_csv,
    fetch_production,
)

TIMEZONE = ZoneInfo("Asia/Tokyo")
MOCKS_DIR = Path(__file__).parent / "mocks" / "JP_area"
LOGGER = getLogger(__name__)

# Zone number → (zone_key, fixture_file, target_date, schema_cols, fixture_rows, target_day_rows)
# fixture_rows: total data rows in the fixture CSV (most are 102-line files = 100 data rows;
#   JP-TH is a daily-rolling realtime file capped at 48 rows for the day).
# target_day_rows: how many rows of the target date the fixture contains after parsing
#   (all are 48 at 30-min × 24h, except JP-KY which starts at 0:30 and uses 24:00 for the
#   last slot — that 24:00 rolls over into the next day via the datetime parser, so only 47
#   rows remain on the target day).
ZONE_FIXTURES = {
    "01": (
        "JP-HKD",
        "eria_jukyu_202604_01.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        22,
        100,
        48,
    ),
    "02": (
        "JP-TH",
        "realtime_jukyu_20260415_02.csv",
        datetime(2026, 4, 15, tzinfo=TIMEZONE),
        22,
        48,
        43,
    ),  # last 5 rows empty (download captured mid-day)
    "03": (
        "JP-TK",
        "eria_jukyu_202604_03.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        20,
        100,
        48,
    ),
    "04": (
        "JP-CB",
        "eria_jukyu_202603_04.csv",
        datetime(2026, 3, 1, tzinfo=TIMEZONE),
        20,
        100,
        48,
    ),
    "05": (
        "JP-HR",
        "eria_jukyu_202604_05.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        22,
        100,
        48,
    ),
    "06": (
        "JP-KN",
        "eria_jukyu_202604_06.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        20,
        100,
        48,
    ),
    "07": (
        "JP-CG",
        "eria_jukyu_202604_07.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        22,
        100,
        48,
    ),
    "08": (
        "JP-SK",
        "eria_jukyu_202604_08.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        20,
        100,
        48,
    ),
    "09": (
        "JP-KY",
        "eria_jukyu_202604_09.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        20,
        100,
        47,
    ),
    "10": (
        "JP-ON",
        "eria_jukyu_202604_10.csv",
        datetime(2026, 4, 1, tzinfo=TIMEZONE),
        22,
        100,
        48,
    ),
}

# First-row expected values per zone (from real data):
# (nuclear, gas, coal, oil, other_thermal, hydro, geothermal, biomass, solar, wind, pumped, battery, other)
EXPECTED_FIRST_ROW = {
    "01": (0, 367, 1079, 326, 210, 396, 10, 296, 0, 275, 60, -5, 0),  # JP-HKD
    "02": (
        0,
        1711,
        4120,
        0,
        291,
        1887,
        161,
        593,
        None,
        185,
        -1,
        -1,
        25,
    ),  # JP-TH (solar=-3 → None: ProductionMix rejects negatives)
    "03": (1319, 9737, 6769, 115, 1438, 1224, 0, 448, 0, 418, 0, 2, 182),  # JP-TK
    "04": (0, 3492, 3532, 0, 436, 708, 2, 608, 0, 220, 442, 0, 122),  # JP-CB
    "05": (0, 127, 957, 0, 2, 1230, 0, 90, 0, 29, 0, 0, 140),  # JP-HR
    "06": (4610, 3003, 1489, 6, 563, 1308, 0, 186, 0, 94, -725, -15, 75),  # JP-KN
    "07": (0, 419, 3750, 52, 413, 504, 0, 365, 0, 14, -3, 0, 0),  # JP-CG
    "08": (
        880,
        253,
        1403,
        0,
        164,
        366,
        None,
        290,
        0,
        132,
        0,
        0,
        None,
    ),  # JP-SK (NaN → None for geothermal, battery)
    "09": (3662, 734, 3068, 76, 292, 298, 164, 900, 4, 52, 122, -16, 204),  # JP-KY
    "10": (0, 151, 429, 81, 0, 1, 0, 47, 0, 5, 0, 0, 0),  # JP-ON
}


# ─── _read_area_csv tests (all 10 zones) ─────────────────────────────────────


def _read_fixture(zone_num: str) -> tuple:
    """Read fixture for a zone number, return (zone_key, df, target_date)."""
    zone_key, filename, target, _, _, _ = ZONE_FIXTURES[zone_num]
    content = (MOCKS_DIR / filename).read_bytes()
    df = _read_area_csv(content)
    return zone_key, df, target


def test_read_area_csv_zone_01_hkd():
    """JP-HKD (01): Shift-JIS, 22 columns, zero-padded dates."""
    _, df, _ = _read_fixture("01")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns  # 22-col specific
    assert len(df) == ZONE_FIXTURES["01"][4]  # 100 data rows


def test_read_area_csv_zone_02_th():
    """JP-TH (02): Shift-JIS, 22 columns, realtime filename (daily-rolling file)."""
    _, df, _ = _read_fixture("02")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    # Realtime files are single-day only (48 rows at 30-min intervals)
    assert len(df) == ZONE_FIXTURES["02"][4]  # 48


def test_read_area_csv_zone_03_tk():
    """JP-TK (03): UTF-8 encoding, 20 columns."""
    _, df, _ = _read_fixture("03")
    assert "DATE" in df.columns
    assert "火力出力制御量" not in df.columns  # 20-col
    assert len(df) == ZONE_FIXTURES["03"][4]


def test_read_area_csv_zone_04_cb():
    """JP-CB (04): Shift-JIS, 20 columns, March 2026 data."""
    _, df, _ = _read_fixture("04")
    assert "DATE" in df.columns
    assert len(df) == ZONE_FIXTURES["04"][4]


def test_read_area_csv_zone_05_hr():
    """JP-HR (05): Shift-JIS, 22 columns."""
    _, df, _ = _read_fixture("05")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == ZONE_FIXTURES["05"][4]


def test_read_area_csv_zone_06_kn():
    """JP-KN (06): Shift-JIS, 20 columns, full-width parens normalised."""
    _, df, _ = _read_fixture("06")
    assert "火力(LNG)" in df.columns  # normalised from 火力（LNG）
    assert "火力（LNG）" not in df.columns
    assert len(df) == ZONE_FIXTURES["06"][4]


def test_read_area_csv_zone_07_cg():
    """JP-CG (07): Shift-JIS, 22 columns."""
    _, df, _ = _read_fixture("07")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == ZONE_FIXTURES["07"][4]


def test_read_area_csv_zone_08_sk():
    """JP-SK (08): Shift-JIS, 20 columns, has NaN cells (地熱, 蓄電池)."""
    _, df, _ = _read_fixture("08")
    assert "DATE" in df.columns
    assert len(df) == ZONE_FIXTURES["08"][4]


def test_read_area_csv_zone_09_ky():
    """JP-KY (09): Shift-JIS, 20 columns, quoted values, full-width ＬＮＧ → LNG."""
    _, df, _ = _read_fixture("09")
    assert "火力(LNG)" in df.columns  # normalised from 火力（ＬＮＧ）
    assert len(df) == ZONE_FIXTURES["09"][4]


def test_read_area_csv_zone_10_on():
    """JP-ON (10): Shift-JIS, 22 columns."""
    _, df, _ = _read_fixture("10")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == ZONE_FIXTURES["10"][4]


# ─── _parse_area_datetime tests ──────────────────────────────────────────────


def test_parse_datetime_slash_padded():
    """YYYY/MM/DD HH:MM (JP-HKD, JP-CB, JP-CG style)."""
    dt = _parse_area_datetime("2026/04/01", "00:30")
    assert dt == datetime(2026, 4, 1, 0, 30, tzinfo=TIMEZONE)


def test_parse_datetime_slash_unpadded():
    """YYYY/M/D H:MM (most zones)."""
    dt = _parse_area_datetime("2026/4/1", "0:00")
    assert dt == datetime(2026, 4, 1, 0, 0, tzinfo=TIMEZONE)


def test_parse_datetime_compact():
    """YYYYMMDD H:MM (JP-KY style)."""
    dt = _parse_area_datetime("20260401", "0:30")
    assert dt == datetime(2026, 4, 1, 0, 30, tzinfo=TIMEZONE)


def test_parse_datetime_24_00():
    """24:00 wraps to 00:00 of the next day."""
    dt = _parse_area_datetime("2026/04/01", "24:00")
    assert dt == datetime(2026, 4, 2, 0, 0, tzinfo=TIMEZONE)


# ─── Production breakdown tests (all 10 zones) ──────────────────────────────


def _assert_production(zone_num: str):
    """Generic assertion: parse fixture for a zone and verify first-row values."""
    zone_key, df, target = _read_fixture(zone_num)
    source = f"test-{zone_key}"
    result = _df_to_production_breakdown_list(df, zone_key, source, target, LOGGER)

    expected_rows = ZONE_FIXTURES[zone_num][5]  # target_day_rows
    assert len(result) == expected_rows, (
        f"Expected {expected_rows} rows for zone {zone_num} ({zone_key}) "
        f"on {target.date()}, got {len(result)}"
    )
    # All returned events are for the target date (filtering works)
    target_day = target.date()
    for event in result:
        assert event["datetime"].date() == target_day, (
            f"{zone_key} event on wrong date: {event['datetime']}"
        )

    first = result[0]
    assert first["zoneKey"] == zone_key
    assert first["source"] == source

    expected = EXPECTED_FIRST_ROW[zone_num]
    (
        nuclear,
        gas,
        coal,
        oil,
        other_thermal,
        hydro,
        geothermal,
        biomass,
        solar,
        wind,
        pumped,
        battery,
        other,
    ) = expected

    prod = first["production"]

    # Production modes — None means "value was negative in CSV, ProductionMix
    # rejected it" or "cell was empty (NaN)". Both are correct behavior.
    for mode_name, expected_val in [
        ("nuclear", nuclear),
        ("gas", gas),
        ("coal", coal),
        ("oil", oil),
        ("hydro", hydro),
        ("biomass", biomass),
        ("solar", solar),
        ("wind", wind),
        ("geothermal", geothermal),
    ]:
        if expected_val is not None:
            assert prod.get(mode_name) == expected_val, (
                f"{zone_key} {mode_name}: got {prod.get(mode_name)}, expected {expected_val}"
            )
        else:
            assert prod.get(mode_name) is None, (
                f"{zone_key} {mode_name}: expected None, got {prod.get(mode_name)}"
            )

    # unknown = 火力(その他) + その他
    if other_thermal is not None and other is not None:
        expected_unknown = other_thermal + other
        assert prod.get("unknown") == expected_unknown, f"{zone_key} unknown"

    # Storage: CSV positive=generating → EM negative=discharging, and vice versa
    storage = first.get("storage")
    if pumped is not None and pumped != 0:
        assert storage is not None, f"{zone_key} should have storage"
        assert storage.get("hydro") == -pumped, f"{zone_key} storage.hydro"
    if battery is not None and battery != 0:
        assert storage is not None, f"{zone_key} should have storage"
        assert storage.get("battery") == -battery, f"{zone_key} storage.battery"

    return result


def test_production_zone_01_hkd():
    """JP-HKD (01): 22-col, all thermal + wind + hydro, pumped + battery."""
    _assert_production("01")


def test_production_zone_02_th():
    """JP-TH (02): 22-col realtime, negative solar (nighttime artifact)."""
    _assert_production("02")


def test_production_zone_03_tk():
    """JP-TK (03): UTF-8, largest demand, nuclear active."""
    _assert_production("03")


def test_production_zone_04_cb():
    """JP-CB (04): March 2026 data, pumped storage active."""
    _assert_production("04")


def test_production_zone_05_hr():
    """JP-HR (05): 22-col, large hydro, big 'other' (140 MW)."""
    _assert_production("05")


def test_production_zone_06_kn():
    """JP-KN (06): full-width parens, large nuclear (4610 MW), pumped charging."""
    result = _assert_production("06")
    first = result[0]
    # Verify pumped storage sign: 揚水=-725 (pumping) → storage.hydro=+725 (charging)
    assert first["storage"]["hydro"] == 725


def test_production_zone_07_cg():
    """JP-CG (07): 22-col, no nuclear, pumped discharging (-3)."""
    _assert_production("07")


def test_production_zone_08_sk():
    """JP-SK (08): NaN cells for geothermal and battery (empty in CSV)."""
    zone_key, df, target = _read_fixture("08")
    result = _df_to_production_breakdown_list(df, zone_key, "test", target, LOGGER)
    assert len(result) == ZONE_FIXTURES["08"][5]  # 48 rows for April 1
    first = result[0]
    # Nuclear is active in Shikoku (Ikata)
    assert first["production"]["nuclear"] == 880
    assert first["production"]["coal"] == 1403
    # NaN cells (地熱, 蓄電池) should produce None or be omitted from the mix
    assert first["production"].get("geothermal") is None


def test_production_zone_09_ky():
    """JP-KY (09): quoted CSV, compact date, full-width LNG."""
    result = _assert_production("09")
    first = result[0]
    assert first["production"]["nuclear"] == 3662
    assert first["production"]["gas"] == 734  # normalised from ＬＮＧ


def test_production_zone_10_on():
    """JP-ON (10): 22-col, small island, no nuclear, zero storage."""
    result = _assert_production("10")
    first = result[0]
    assert first["production"]["nuclear"] == 0
    # Storage exists but all values are zero (揚水=0, 蓄電池=0 → negated to -0.0)
    storage = first.get("storage")
    if storage is not None:
        assert storage.get("hydro") == 0 or storage.get("hydro") == -0.0
        assert storage.get("battery") == 0 or storage.get("battery") == -0.0


def test_production_filters_to_target_date():
    """Only rows matching the target date should be returned."""
    _, df, _ = _read_fixture("01")
    # Use a date not in the fixture
    wrong_date = datetime(2026, 4, 15, tzinfo=TIMEZONE)
    result = _df_to_production_breakdown_list(df, "JP-HKD", "test", wrong_date, LOGGER)
    assert len(result) == 0


# ─── Routing tests ───────────────────────────────────────────────────────────


_ROUTE_NEW = {"JP-HKD": datetime(2024, 4, 1, tzinfo=TIMEZONE)}
_ROUTE_LEGACY = {"JP-HKD": datetime(2016, 4, 1, tzinfo=TIMEZONE)}


def _patch_routing():
    """Patch both date tables and both fetchers; yields (mock_new, mock_legacy)."""
    return (
        patch("electricitymap.contrib.parsers.JP._AREA_CSV_START_DATES", _ROUTE_NEW),
        patch(
            "electricitymap.contrib.parsers.JP._LEGACY_AREA_START_DATES", _ROUTE_LEGACY
        ),
        patch("electricitymap.contrib.parsers.JP._fetch_production_area_csv"),
        patch("electricitymap.contrib.parsers.JP._fetch_production_legacy_area_csv"),
    )


def test_routing_new_format_on_or_after_start():
    """On/after the new-format start, uses the new 30-min path."""
    p_new, p_leg, p_area, p_legacy = _patch_routing()
    with p_new, p_leg, p_area as area, p_legacy as legacy:
        area.return_value = [{"test": "new"}]
        fetch_production(
            "JP-HKD", target_datetime=datetime(2025, 1, 1, tzinfo=TIMEZONE)
        )
        area.assert_called_once()
        legacy.assert_not_called()


def test_routing_legacy_between_floor_and_new_start():
    """Between the legacy floor and the new-format start, uses the legacy path."""
    p_new, p_leg, p_area, p_legacy = _patch_routing()
    with p_new, p_leg, p_area as area, p_legacy as legacy:
        legacy.return_value = [{"test": "legacy"}]
        fetch_production(
            "JP-HKD", target_datetime=datetime(2020, 1, 1, tzinfo=TIMEZONE)
        )
        legacy.assert_called_once()
        area.assert_not_called()


def test_routing_raises_before_legacy_floor():
    """Before the legacy floor there is no data: raise instead of fetching."""
    p_new, p_leg, p_area, p_legacy = _patch_routing()
    with p_new, p_leg, p_area as area, p_legacy as legacy:
        with pytest.raises(NotImplementedError):
            fetch_production(
                "JP-HKD", target_datetime=datetime(2015, 1, 1, tzinfo=TIMEZONE)
            )
        area.assert_not_called()
        legacy.assert_not_called()


def test_routing_jp_sk_has_no_legacy_fallback():
    """JP-SK has no legacy archive: pre-new-format dates raise (real tables)."""
    with (
        patch("electricitymap.contrib.parsers.JP._fetch_production_area_csv"),
        patch(
            "electricitymap.contrib.parsers.JP._fetch_production_legacy_area_csv"
        ) as legacy,
        pytest.raises(NotImplementedError),
    ):
        fetch_production("JP-SK", target_datetime=datetime(2022, 1, 1, tzinfo=TIMEZONE))
    legacy.assert_not_called()


# ─── Completeness checks ─────────────────────────────────────────────────────


def test_column_map_covers_all_production_modes():
    """_AREA_COLUMN_MAP produces all expected Electricity Maps modes."""
    production_modes = {
        field for field, cat in _AREA_COLUMN_MAP.values() if cat == "production"
    }
    expected = {
        "nuclear",
        "gas",
        "coal",
        "oil",
        "hydro",
        "geothermal",
        "biomass",
        "solar",
        "wind",
        "unknown",
    }
    assert production_modes == expected


def test_all_configured_zones_have_source():
    """Every zone in _AREA_CSV_CONFIGS has a non-empty source."""
    for zone_key, config in _AREA_CSV_CONFIGS.items():
        assert config.source, f"{zone_key} has empty source"


# ─── JP-CB ZIP-archive fallback (_fetch_area_csv_content) ────────────────────


def test_fiscal_year_japanese():
    """FY runs Apr–Mar: Jan–Mar belong to the previous calendar year."""
    assert _fiscal_year(datetime(2024, 4, 1, tzinfo=TIMEZONE)) == 2024
    assert _fiscal_year(datetime(2025, 3, 31, tzinfo=TIMEZONE)) == 2024
    assert _fiscal_year(datetime(2024, 3, 1, tzinfo=TIMEZONE)) == 2023
    assert _fiscal_year(datetime(2026, 12, 1, tzinfo=TIMEZONE)) == 2026


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes = b""):
        self.status_code = status_code
        self.content = content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected raise_for_status on {self.status_code}")


class _FakeSession:
    """Session stub returning a queued response per URL substring match."""

    def __init__(self, route):
        self._route = route
        self.urls: list[str] = []

    def get(self, url: str):
        self.urls.append(url)
        return self._route(url)


def test_fetch_area_csv_content_prefers_standalone_csv():
    """When the monthly CSV exists, the ZIP archive is never requested."""
    config = _AREA_CSV_CONFIGS["JP-CB"]
    dt = datetime(2026, 6, 5, tzinfo=TIMEZONE)
    session = _FakeSession(lambda url: _FakeResponse(200, b"csv-bytes"))

    content = _fetch_area_csv_content(config, dt, session)

    assert content == b"csv-bytes"
    assert len(session.urls) == 1
    assert session.urls[0].endswith("eria_jukyu_202606_04.csv")


def test_fetch_area_csv_content_falls_back_to_zip():
    """A 404 on the monthly CSV falls back to the fiscal-year ZIP archive."""
    config = _AREA_CSV_CONFIGS["JP-CB"]
    dt = datetime(2024, 4, 15, tzinfo=TIMEZONE)  # FY2024 archive

    member = "eria_jukyu_202404_04.csv"
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(member, b"archived-csv-bytes")
    zip_bytes = buffer.getvalue()

    def route(url: str):
        if url.endswith(".zip"):
            return _FakeResponse(200, zip_bytes)
        return _FakeResponse(404)

    session = _FakeSession(route)
    content = _fetch_area_csv_content(config, dt, session)

    assert content == b"archived-csv-bytes"
    # Requested the standalone CSV first, then the FY2024 ZIP.
    assert session.urls[0].endswith("eria_jukyu_202404_04.csv")
    assert session.urls[-1].endswith("eria_jukyu_2024.zip")


# ─── Legacy archive parsing ──────────────────────────────────────────────────


def _legacy_breakdown(zone_key: str, text: str, target: datetime) -> list:
    """Parse a legacy fixture (Shift-JIS) with the zone's real config."""
    df = _read_legacy_area_csv(text.encode("shift_jis"))
    return _legacy_df_to_breakdown(
        df, _LEGACY_AREA_CONFIGS[zone_key], zone_key, target, LOGGER
    )


# JP-HKD: split DATE/TIME, kanji time ("N時"), date forward-filled (blank on
# non-midnight rows), single combined 火力 → unknown.
_LEGACY_HKD = (
    "単位[MWh],,,,,,,,,,,,,,\n"
    ",,,供給力,,,,,,,,,,,\n"
    "月日,時刻,エリア需要,原子力,火力,水力,地熱,バイオマス,太陽光実績,太陽光抑制量,風力実績,風力抑制量,揚水,連系線,供給力合計\n"
    ",,,,,,,,,,,,,,\n"
    "2016/4/1,0時,3166,0,2573,474,13,3,0,0,40,0,21,42,3166\n"
    ",1時,3282,0,2640,531,13,3,0,0,34,0,0,61,3282\n"
    "2016/4/2,0時,3000,0,2500,400,13,3,0,0,30,0,10,40,3000\n"
)


def test_legacy_hkd_kanji_time_and_date_ffill():
    result = _legacy_breakdown(
        "JP-HKD", _LEGACY_HKD, datetime(2016, 4, 1, tzinfo=TIMEZONE)
    )
    # Two hours on 2016/4/1; the 1時 row's blank date is carried forward.
    assert len(result) == 2
    assert result[1]["datetime"] == datetime(2016, 4, 1, 1, 0, tzinfo=TIMEZONE)
    first = result[0]
    assert first["datetime"] == datetime(2016, 4, 1, 0, 0, tzinfo=TIMEZONE)
    assert first["source"] == "hepco.co.jp"
    p = first["production"]
    assert p["nuclear"] == 0
    assert p["unknown"] == 2573  # 火力 → unknown
    assert p["hydro"] == 474
    assert p["geothermal"] == 13
    assert p["biomass"] == 3
    assert p["wind"] == 40
    assert first["storage"]["hydro"] == -21  # 揚水 generating → discharging


# JP-TK: 万kWh units (×10 → MWh), demand quoted with a thousands separator.
_LEGACY_TK = (
    "単位[万kWh],,,,,,,,,,,,,,\n"
    "DATE,TIME,東京エリア需要,供給力,,,,,,,,,,,\n"
    ",,,原子力,火力,水力,地熱,バイオマス,太陽光発電実績,太陽光出力制御量,風力発電実績,風力出力制御量,揚水,連系線,合計\n"
    '2016/4/1,0:00,"2,555",0,2258,92,0,2,0,0,3,0,0,201,"2,555"\n'
)


def test_legacy_tk_unit_multiplier():
    result = _legacy_breakdown(
        "JP-TK", _LEGACY_TK, datetime(2016, 4, 1, tzinfo=TIMEZONE)
    )
    assert len(result) == 1
    p = result[0]["production"]
    assert p["unknown"] == 22580  # 2258 × 10
    assert p["hydro"] == 920  # 92 × 10
    assert p["biomass"] == 20
    assert p["wind"] == 30  # 3 × 10


# JP-KN: combined DATE_TIME column; solar/wind share ambiguous 実績 names, so
# positional mapping is essential.
_LEGACY_KN = (
    ",,,,,,,太陽光,太陽光,風力,風力,,\n"
    "DATE_TIME,エリア需要〔MWh〕,原子力〔MWh〕,火力〔MWh〕,水力〔MWh〕,地熱〔MWh〕,バイオマス〔MWh〕,実績〔MWh〕,抑制量〔MWh〕,実績〔MWh〕,抑制量〔MWh〕,揚水〔MWh〕,連系線〔MWh〕\n"
    "2016/4/1 0:00,12918,0,10405,758,0,0,0,0,41,0,89,1625\n"
)


def test_legacy_kn_combined_datetime_and_positional():
    result = _legacy_breakdown(
        "JP-KN", _LEGACY_KN, datetime(2016, 4, 1, tzinfo=TIMEZONE)
    )
    assert len(result) == 1
    p = result[0]["production"]
    assert p["unknown"] == 10405
    assert p["hydro"] == 758
    assert p["wind"] == 41  # second 実績 column, by position
    assert result[0]["storage"]["hydro"] == -89


# JP-ON: islanded reduced schema (no nuclear/geothermal/pumped) AND a multi-line
# quoted header cell (real 2023+ quirk) — the parser must find the first dated row.
_LEGACY_ON = (
    "需給実績公表,,,,,,,,,,,,\n"
    "※注意（単位：MWh）,,,,,,,,,,,,\n"
    ",,,,,,,,,,,,\n"
    "DATE,TIME,エリアの需要実績,,エリアの供給実績,,,,,,,,\n"
    ",,,,火力,水力,ﾊﾞｲｵﾏｽ,太陽光,,風力,,合計,\n"
    ',,,,,,,,"太陽光\n出力制御量",,"風力\n出力制御量",,\n'
    "2016/4/1,0:00,647,,643,1,2,0,0,2,0,647,\n"
)


def test_legacy_on_reduced_schema_and_multiline_header():
    result = _legacy_breakdown(
        "JP-ON", _LEGACY_ON, datetime(2016, 4, 1, tzinfo=TIMEZONE)
    )
    assert len(result) == 1
    p = result[0]["production"]
    assert p["unknown"] == 643
    assert p["hydro"] == 1
    assert p["biomass"] == 2
    assert p["wind"] == 2
    assert p.get("nuclear") is None  # islanded: no nuclear column
    assert not result[0].get("storage")  # no pumped column → empty storage


def test_legacy_breakdown_filters_to_target_day():
    result = _legacy_breakdown(
        "JP-HKD", _LEGACY_HKD, datetime(2016, 4, 2, tzinfo=TIMEZONE)
    )
    assert len(result) == 1
    assert result[0]["datetime"].date() == datetime(2016, 4, 2).date()


# ─── Legacy datetime / fiscal helpers ────────────────────────────────────────


def test_build_legacy_datetime_variants():
    assert _build_legacy_datetime("2016/4/1", "0:30", False) == datetime(
        2016, 4, 1, 0, 30, tzinfo=TIMEZONE
    )
    assert _build_legacy_datetime("2016/04/01", "13:00", False) == datetime(
        2016, 4, 1, 13, 0, tzinfo=TIMEZONE
    )
    assert _build_legacy_datetime("2016/4/1", "5時", True) == datetime(
        2016, 4, 1, 5, 0, tzinfo=TIMEZONE
    )


def test_fiscal_quarter():
    months_to_q = {4: 1, 6: 1, 7: 2, 9: 2, 10: 3, 12: 3, 1: 4, 3: 4}
    for month, quarter in months_to_q.items():
        assert _fiscal_quarter(datetime(2020, month, 15, tzinfo=TIMEZONE)) == quarter


# ─── Legacy config completeness ──────────────────────────────────────────────


def test_legacy_configs_and_start_dates_aligned():
    assert set(_LEGACY_AREA_CONFIGS) == set(_LEGACY_AREA_START_DATES)


def test_legacy_jp_sk_has_no_archive():
    """JP-SK publishes no per-fuel history before the new format."""
    assert "JP-SK" not in _LEGACY_AREA_CONFIGS
    assert "JP-SK" not in _LEGACY_AREA_START_DATES


def test_legacy_floor_precedes_new_format_start():
    """Every legacy zone is also a new-format zone, and its floor is earlier."""
    for zone_key, floor in _LEGACY_AREA_START_DATES.items():
        assert zone_key in _AREA_CSV_START_DATES
        assert floor < _AREA_CSV_START_DATES[zone_key]


def test_legacy_configs_have_source():
    for zone_key, config in _LEGACY_AREA_CONFIGS.items():
        assert config.source, f"{zone_key} legacy config has empty source"


# ─── Legacy URL building, value parsing, and fetch edge cases ─────────────────


def test_hr_legacy_url_quarterly_then_monthly():
    """Hokuriku: calendar-quarter files before 2018-10, monthly after."""
    # Quarterly (before 2018-10): name is {year}{quarter_start:02d}_{quarter_end:02d}.
    assert _hr_legacy_url(datetime(2016, 5, 15, tzinfo=TIMEZONE)).endswith(
        "area_jisseki_rikuden201604_06.csv"  # May → Apr–Jun 2016
    )
    assert _hr_legacy_url(datetime(2018, 9, 30, tzinfo=TIMEZONE)).endswith(
        "area_jisseki_rikuden201807_09.csv"  # Sep → Jul–Sep 2018
    )
    assert _hr_legacy_url(datetime(2017, 1, 10, tzinfo=TIMEZONE)).endswith(
        "area_jisseki_rikuden201701_03.csv"  # Jan → Jan–Mar 2017
    )
    # Monthly (2018-10 onward).
    assert _hr_legacy_url(datetime(2018, 10, 1, tzinfo=TIMEZONE)).endswith(
        "area_jisseki_rikuden201810.csv"
    )
    assert _hr_legacy_url(datetime(2019, 5, 20, tzinfo=TIMEZONE)).endswith(
        "area_jisseki_rikuden201905.csv"
    )


def test_legacy_value_to_float():
    # Missing markers (blanks, ASCII/full-width dashes used as "no data").
    for missing in ("", "-", "−", "―", "—", "nan"):
        assert _legacy_value_to_float(missing) is None
    assert _legacy_value_to_float(float("nan")) is None
    # Numbers, including thousands separators, decimals, negatives, and quotes.
    assert _legacy_value_to_float("1,234") == 1234.0
    assert _legacy_value_to_float("123.4") == 123.4
    assert _legacy_value_to_float("-305") == -305.0  # pumped-storage charging
    assert _legacy_value_to_float('"42"') == 42.0


# Combined-datetime fixture with NEGATIVE 揚水 (pumping) to exercise the
# charging-sign path: CSV negative (pumping) → EM positive (charging).
_LEGACY_PUMPING = (
    ",,,,,,,太陽光,太陽光,風力,風力,,\n"
    "DATE_TIME,エリア需要〔MWh〕,原子力〔MWh〕,火力〔MWh〕,水力〔MWh〕,地熱〔MWh〕,バイオマス〔MWh〕,実績〔MWh〕,抑制量〔MWh〕,実績〔MWh〕,抑制量〔MWh〕,揚水〔MWh〕,連系線〔MWh〕\n"
    "2016/4/1 0:00,12000,0,9000,500,0,0,0,0,30,0,-305,1000\n"
)


def test_legacy_storage_charging_sign():
    result = _legacy_breakdown(
        "JP-KN", _LEGACY_PUMPING, datetime(2016, 4, 1, tzinfo=TIMEZONE)
    )
    assert len(result) == 1
    # 揚水 = -305 (pumping/charging) → storage.hydro = +305.
    assert result[0]["storage"]["hydro"] == 305


def test_legacy_breakdown_returns_empty_when_no_data_rows():
    """A header-only file (no dated rows) yields no events instead of erroring."""
    header_only = (
        "単位[MWh],,,,,,,,,,,,,,\n"
        "月日,時刻,エリア需要,原子力,火力,水力,地熱,バイオマス,太陽光実績,太陽光抑制量,風力実績,風力抑制量,揚水,連系線,供給力合計\n"
        ",,,,,,,,,,,,,,\n"
    )
    result = _legacy_breakdown(
        "JP-HKD", header_only, datetime(2016, 4, 1, tzinfo=TIMEZONE)
    )
    assert result == []


class _HeaderRecordingSession:
    """Session stub that records the headers passed to .get()."""

    def __init__(self, content: bytes):
        self._content = content
        self.url: str | None = None
        self.headers: dict | None = None

    def get(self, url: str, headers: dict | None = None):
        self.url = url
        self.headers = headers or {}
        return _FakeResponse(200, self._content)


def test_legacy_fetch_sends_referer_for_kansai():
    """JP-KN requires a Referer header; the fetch must send it (and the URL)."""
    session = _HeaderRecordingSession(_LEGACY_KN.encode("shift_jis"))
    result = _fetch_production_legacy_area_csv(
        "JP-KN", datetime(2016, 4, 1, tzinfo=TIMEZONE), session, LOGGER
    )
    assert session.url.endswith("area_jyukyu_jisseki_2016.csv")
    assert session.headers["Referer"] == (
        "https://www.kansai-td.co.jp/denkiyoho/area-performance/past.html"
    )
    # Sanity: parsing still produced the day's events through the full fetch path.
    assert len(result) == 1


def test_legacy_fetch_omits_referer_when_not_configured():
    """Zones without a referer (e.g. JP-HKD) send only a User-Agent."""
    session = _HeaderRecordingSession(_LEGACY_HKD.encode("shift_jis"))
    _fetch_production_legacy_area_csv(
        "JP-HKD", datetime(2016, 4, 1, tzinfo=TIMEZONE), session, LOGGER
    )
    assert session.url.endswith("sup_dem_results_2016_1q.csv")
    assert "Referer" not in session.headers
    assert "User-Agent" in session.headers
