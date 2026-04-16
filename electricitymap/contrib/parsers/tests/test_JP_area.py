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
from logging import getLogger
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from electricitymap.contrib.parsers.JP import (
    _AREA_COLUMN_MAP,
    _AREA_CSV_CONFIGS,
    _df_to_production_breakdown_list,
    _parse_area_datetime,
    _read_area_csv,
    fetch_production,
)

TIMEZONE = ZoneInfo("Asia/Tokyo")
MOCKS_DIR = Path(__file__).parent / "mocks" / "JP_area"
LOGGER = getLogger(__name__)

# Zone number → (zone_key, fixture_file, target_date, schema_cols)
ZONE_FIXTURES = {
    "01": ("JP-HKD", "eria_jukyu_202604_01.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 22),
    "02": ("JP-TH", "realtime_jukyu_20260415_02.csv", datetime(2026, 4, 15, tzinfo=TIMEZONE), 22),
    "03": ("JP-TK", "eria_jukyu_202604_03.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 20),
    "04": ("JP-CB", "eria_jukyu_202603_04.csv", datetime(2026, 3, 1, tzinfo=TIMEZONE), 20),
    "05": ("JP-HR", "eria_jukyu_202604_05.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 22),
    "06": ("JP-KN", "eria_jukyu_202604_06.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 20),
    "07": ("JP-CG", "eria_jukyu_202604_07.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 22),
    "08": ("JP-SK", "eria_jukyu_202604_08.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 20),
    "09": ("JP-KY", "eria_jukyu_202604_09.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 20),
    "10": ("JP-ON", "eria_jukyu_202604_10.csv", datetime(2026, 4, 1, tzinfo=TIMEZONE), 22),
}

# First-row expected values per zone (from real data):
# (nuclear, gas, coal, oil, other_thermal, hydro, geothermal, biomass, solar, wind, pumped, battery, other)
EXPECTED_FIRST_ROW = {
    "01": (0, 367, 1079, 326, 210, 396, 10, 296, 0, 275, 60, -5, 0),       # JP-HKD
    "02": (0, 1711, 4120, 0, 291, 1887, 161, 593, None, 185, -1, -1, 25),    # JP-TH (solar=-3 → None: ProductionMix rejects negatives)
    "03": (1319, 9737, 6769, 115, 1438, 1224, 0, 448, 0, 418, 0, 2, 182),   # JP-TK
    "04": (0, 3492, 3532, 0, 436, 708, 2, 608, 0, 220, 442, 0, 122),        # JP-CB
    "05": (0, 127, 957, 0, 2, 1230, 0, 90, 0, 29, 0, 0, 140),              # JP-HR
    "06": (4610, 3003, 1489, 6, 563, 1308, 0, 186, 0, 94, -725, -15, 75),   # JP-KN
    "07": (0, 419, 3750, 52, 413, 504, 0, 365, 0, 14, -3, 0, 0),           # JP-CG
    "08": (880, 253, 1403, 0, 164, 366, None, 290, 0, 132, 0, 0, None),     # JP-SK (NaN → None for geothermal, battery)
    "09": (3662, 734, 3068, 76, 292, 298, 164, 900, 4, 52, 122, -16, 204),  # JP-KY
    "10": (0, 151, 429, 81, 0, 1, 0, 47, 0, 5, 0, 0, 0),                   # JP-ON
}


# ─── _read_area_csv tests (all 10 zones) ─────────────────────────────────────


def _read_fixture(zone_num: str) -> tuple:
    """Read fixture for a zone number, return (zone_key, df, target_date)."""
    zone_key, filename, target, _ = ZONE_FIXTURES[zone_num]
    content = (MOCKS_DIR / filename).read_bytes()
    df = _read_area_csv(content)
    return zone_key, df, target


def test_read_area_csv_zone_01_hkd():
    """JP-HKD (01): Shift-JIS, 22 columns, zero-padded dates."""
    _, df, _ = _read_fixture("01")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns  # 22-col specific
    assert len(df) == 2


def test_read_area_csv_zone_02_th():
    """JP-TH (02): Shift-JIS, 22 columns, realtime filename."""
    _, df, _ = _read_fixture("02")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == 2


def test_read_area_csv_zone_03_tk():
    """JP-TK (03): UTF-8 encoding, 20 columns."""
    _, df, _ = _read_fixture("03")
    assert "DATE" in df.columns
    assert "火力出力制御量" not in df.columns  # 20-col
    assert len(df) == 2


def test_read_area_csv_zone_04_cb():
    """JP-CB (04): Shift-JIS, 20 columns, March 2026 data."""
    _, df, _ = _read_fixture("04")
    assert "DATE" in df.columns
    assert len(df) == 2


def test_read_area_csv_zone_05_hr():
    """JP-HR (05): Shift-JIS, 22 columns."""
    _, df, _ = _read_fixture("05")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == 2


def test_read_area_csv_zone_06_kn():
    """JP-KN (06): Shift-JIS, 20 columns, full-width parens normalised."""
    _, df, _ = _read_fixture("06")
    assert "火力(LNG)" in df.columns  # normalised from 火力（LNG）
    assert "火力（LNG）" not in df.columns
    assert len(df) == 2


def test_read_area_csv_zone_07_cg():
    """JP-CG (07): Shift-JIS, 22 columns."""
    _, df, _ = _read_fixture("07")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == 2


def test_read_area_csv_zone_08_sk():
    """JP-SK (08): Shift-JIS, 20 columns, has NaN cells (地熱, 蓄電池)."""
    _, df, _ = _read_fixture("08")
    assert "DATE" in df.columns
    assert len(df) == 2


def test_read_area_csv_zone_09_ky():
    """JP-KY (09): Shift-JIS, 20 columns, quoted values, full-width ＬＮＧ → LNG."""
    _, df, _ = _read_fixture("09")
    assert "火力(LNG)" in df.columns  # normalised from 火力（ＬＮＧ）
    assert len(df) == 2


def test_read_area_csv_zone_10_on():
    """JP-ON (10): Shift-JIS, 22 columns."""
    _, df, _ = _read_fixture("10")
    assert "DATE" in df.columns
    assert "火力出力制御量" in df.columns
    assert len(df) == 2


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

    assert len(result) == 2, f"Expected 2 rows for zone {zone_num} ({zone_key})"
    first = result[0]
    assert first["zoneKey"] == zone_key
    assert first["source"] == source

    expected = EXPECTED_FIRST_ROW[zone_num]
    (nuclear, gas, coal, oil, other_thermal, hydro, geothermal, biomass,
     solar, wind, pumped, battery, other) = expected

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
    assert len(result) == 2
    first = result[0]
    # Nuclear is active in Shikoku (Ikata)
    assert first["production"]["nuclear"] == 880
    assert first["production"]["coal"] == 1403


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


def test_routing_legacy_when_no_start_date():
    """With empty _AREA_CSV_START_DATES, always uses legacy path."""
    with patch(
        "electricitymap.contrib.parsers.JP._AREA_CSV_START_DATES", {}
    ), patch(
        "electricitymap.contrib.parsers.JP._fetch_production_consumption_based"
    ) as mock_legacy, patch(
        "electricitymap.contrib.parsers.JP._fetch_production_area_csv"
    ) as mock_area:
        mock_legacy.return_value = [{"test": "legacy"}]
        fetch_production("JP-HKD", target_datetime=datetime(2026, 4, 1, tzinfo=TIMEZONE))
        mock_legacy.assert_called_once()
        mock_area.assert_not_called()


def test_routing_area_csv_after_start_date():
    """After the start date, uses area-CSV path."""
    start = datetime(2025, 4, 1, tzinfo=TIMEZONE)
    with patch(
        "electricitymap.contrib.parsers.JP._AREA_CSV_START_DATES",
        {"JP-HKD": start},
    ), patch(
        "electricitymap.contrib.parsers.JP._fetch_production_consumption_based"
    ) as mock_legacy, patch(
        "electricitymap.contrib.parsers.JP._fetch_production_area_csv"
    ) as mock_area:
        mock_area.return_value = [{"test": "area"}]
        fetch_production("JP-HKD", target_datetime=datetime(2026, 4, 1, tzinfo=TIMEZONE))
        mock_area.assert_called_once()
        mock_legacy.assert_not_called()


def test_routing_legacy_before_start_date():
    """Before the start date, uses legacy path even when zone is configured."""
    start = datetime(2025, 4, 1, tzinfo=TIMEZONE)
    with patch(
        "electricitymap.contrib.parsers.JP._AREA_CSV_START_DATES",
        {"JP-HKD": start},
    ), patch(
        "electricitymap.contrib.parsers.JP._fetch_production_consumption_based"
    ) as mock_legacy, patch(
        "electricitymap.contrib.parsers.JP._fetch_production_area_csv"
    ) as mock_area:
        mock_legacy.return_value = [{"test": "legacy"}]
        fetch_production("JP-HKD", target_datetime=datetime(2024, 6, 1, tzinfo=TIMEZONE))
        mock_legacy.assert_called_once()
        mock_area.assert_not_called()


# ─── Completeness checks ─────────────────────────────────────────────────────


def test_column_map_covers_all_production_modes():
    """_AREA_COLUMN_MAP produces all expected Electricity Maps modes."""
    production_modes = {
        field for field, cat in _AREA_COLUMN_MAP.values() if cat == "production"
    }
    expected = {"nuclear", "gas", "coal", "oil", "hydro", "geothermal", "biomass", "solar", "wind", "unknown"}
    assert production_modes == expected


def test_all_configured_zones_have_source():
    """Every zone in _AREA_CSV_CONFIGS has a non-empty source."""
    for zone_key, config in _AREA_CSV_CONFIGS.items():
        assert config.source, f"{zone_key} has empty source"
