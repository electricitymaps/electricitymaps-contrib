#!/usr/bin/env python3
import csv
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from logging import Logger, getLogger
from typing import Any
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.types import ZoneKey

# Zone key → OCCTO zone number → TSO name
# JP-HKD : 01 : Hokkaido Electric (HEPCO)
# JP-TH  : 02 : Tohoku Electric
# JP-TK  : 03 : Tokyo Electric (TEPCO)
# JP-CB  : 04 : Chubu Electric (ChuDEN)
# JP-HR  : 05 : Hokuriku Electric (Rikuden)
# JP-KN  : 06 : Kansai Transmission & Distribution
# JP-CG  : 07 : Chugoku Electric (Energia)
# JP-SK  : 08 : Shikoku Electric (Yonden)
# JP-KY  : 09 : Kyushu Electric (Kyuden)
# JP-ON  : 10 : Okinawa Electric (OEPC)

ZONE_INFO = ZoneInfo("Asia/Tokyo")

# Some TSO sites filter the default python-requests User-Agent.
_REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}

# ─── Area CSV: per-zone data availability floor ──────────────────────────────
# Each date is the first month the new 30-min eria_jukyu format is published AND
# its fuel breakdown is actually populated (verified against the data, not just
# the file's existence). Earlier dates fall back to the legacy archive below.
# JP-TK and JP-HR publish the new file a few months before they start filling in
# the thermal columns, so their floors are set to the first fully-populated month
# (their empty earlier months are covered correctly by the legacy archive).
_AREA_CSV_START_DATES: dict[str, datetime] = {
    "JP-HKD": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    "JP-TH": datetime(2024, 2, 1, tzinfo=ZONE_INFO),
    "JP-TK": datetime(2024, 1, 1, tzinfo=ZONE_INFO),  # 2023-11/12 thermal all 0
    "JP-CB": datetime(2024, 3, 1, tzinfo=ZONE_INFO),
    "JP-HR": datetime(2024, 4, 1, tzinfo=ZONE_INFO),  # 2024-03 thermal all 0
    "JP-KN": datetime(2024, 1, 1, tzinfo=ZONE_INFO),
    "JP-CG": datetime(2024, 2, 1, tzinfo=ZONE_INFO),
    "JP-SK": datetime(2024, 3, 1, tzinfo=ZONE_INFO),
    "JP-KY": datetime(2023, 10, 1, tzinfo=ZONE_INFO),
    "JP-ON": datetime(2024, 2, 1, tzinfo=ZONE_INFO),
}

# ─── Legacy area archive: earlier (pre-new-format) per-fuel data ──────────────
# Before the new 30-min eria_jukyu format, each TSO published an older hourly
# "area supply-demand" archive going back to ~FY2016 (JP-KY only to FY2019).
# These are COARSER: hourly (not 30-min), thermal is a single combined column
# (mapped to "unknown" — no LNG/coal/oil split), and there is no battery.
# Used only for dates before _AREA_CSV_START_DATES and on/after the floor below.
#
# NOTE — JP-SK (Shikoku) is intentionally absent: Yonden publishes NO per-fuel
# history before the new format (2024-03). Only demand-only (to 2016) and
# area-totals-only (to 2022) archives exist, neither with a generation mix, so
# JP-SK simply has no production data before 2024-03.
_LEGACY_AREA_START_DATES: dict[str, datetime] = {
    "JP-HKD": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-TH": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-TK": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-CB": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-HR": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-KN": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-CG": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
    "JP-KY": datetime(2019, 4, 1, tzinfo=ZONE_INFO),
    "JP-ON": datetime(2016, 4, 1, tzinfo=ZONE_INFO),
}


@dataclass(frozen=True)
class _AreaCsvConfig:
    url_builder: Callable[[datetime], str]
    source: str
    # Some TSOs (JP-CB) only keep the latest months as standalone CSVs and
    # bundle older months into a ZIP archive. When the monthly URL 404s, fetch
    # this ZIP and read the member named by zip_member_builder.
    zip_url_builder: Callable[[datetime], str] | None = None
    zip_member_builder: Callable[[datetime], str] | None = None
    # Some TSOs (JP-TH) publish the monthly CSV with a multi-week lag and keep
    # recent days in per-day "realtime" files instead. When the monthly URL
    # 404s, fetch the target date's daily file (same format).
    daily_url_builder: Callable[[datetime], str] | None = None
    # JP-KY labels each 30-min interval by its END (0:30 … 24:00) where every
    # other TSO labels the START (0:00 … 23:30). Shift to align.
    datetime_offset: timedelta = timedelta()


def _monthly(base: str, suffix: str) -> Callable[[datetime], str]:
    """Standard monthly URL pattern: base + YYYYMM + suffix."""
    return lambda dt: f"{base}{dt.strftime('%Y%m')}{suffix}"


def _fiscal_year(dt: datetime) -> int:
    """Japanese fiscal year (Apr–Mar) that contains dt."""
    return dt.year if dt.month >= 4 else dt.year - 1


def _fiscal_quarter(dt: datetime) -> int:
    """Japanese fiscal quarter: Q1=Apr–Jun, Q2=Jul–Sep, Q3=Oct–Dec, Q4=Jan–Mar."""
    return ((dt.month - 4) % 12) // 3 + 1


_AREA_CSV_CONFIGS: dict[str, _AreaCsvConfig] = {
    "JP-HKD": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.hepco.co.jp/network/con_service/public_document/"
            "supply_demand_results/csv/eria_jukyu_",
            "_01.csv",
        ),
        source="hepco.co.jp",
    ),
    "JP-TH": _AreaCsvConfig(
        url_builder=_monthly(
            "https://setsuden.nw.tohoku-epco.co.jp/common/demand/eria_jukyu_",
            "_02.csv",
        ),
        source="setsuden.nw.tohoku-epco.co.jp",
        # Tohoku only publishes the monthly file weeks after month end; recent
        # days (current + previous month) live in per-day realtime files.
        daily_url_builder=lambda dt: (
            "https://setsuden.nw.tohoku-epco.co.jp/common/demand/realtime_jukyu/"
            f"realtime_jukyu_{dt.strftime('%Y%m%d')}_02.csv"
        ),
    ),
    "JP-TK": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.tepco.co.jp/forecast/html/images/eria_jukyu_", "_03.csv"
        ),
        source="tepco.co.jp",
    ),
    "JP-CB": _AreaCsvConfig(
        url_builder=_monthly(
            "https://powergrid.chuden.co.jp/denki_yoho_content_data/eria_jukyu_",
            "_04.csv",
        ),
        source="powergrid.chuden.co.jp",
        # Chubu keeps only the latest ~2 months as standalone CSVs; older months
        # live in per-fiscal-year ZIPs, e.g. eria_jukyu_2024.zip (Apr 2024–Mar 2025).
        zip_url_builder=lambda dt: (
            "https://powergrid.chuden.co.jp/denki_yoho_content_data/"
            f"eria_jukyu_{_fiscal_year(dt)}.zip"
        ),
        zip_member_builder=lambda dt: f"eria_jukyu_{dt.strftime('%Y%m')}_04.csv",
    ),
    "JP-HR": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.rikuden.co.jp/nw/denki-yoho/csv/eria_jukyu_", "_05.csv"
        ),
        source="rikuden.co.jp",
    ),
    "JP-KN": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.kansai-td.co.jp/interchange/denkiyoho/"
            "area-performance/eria_jukyu_",
            "_06.csv",
        ),
        source="kansai-td.co.jp",
    ),
    "JP-CG": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.energia.co.jp/nw/jukyuu/sys/eria_jukyu_", "_07.csv"
        ),
        source="energia.co.jp",
    ),
    "JP-SK": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.yonden.co.jp/nw/supply_demand/csv/eria_jukyu_", "_08.csv"
        ),
        source="yonden.co.jp",
    ),
    "JP-KY": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.kyuden.co.jp/td_area_jukyu/csv/eria_jukyu_", "_09.csv"
        ),
        source="kyuden.co.jp",
        # Kyushu's rows are end-of-interval labelled (0:30 … 24:00); shift back
        # 30 min to start-of-interval like the other zones. (Kyushu's LEGACY
        # archive is start-labelled — verified — so no offset there.)
        datetime_offset=timedelta(minutes=-30),
    ),
    "JP-ON": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.okiden.co.jp/business-support/service/"
            "supply-and-demand/csv/eria_jukyu_",
            "_10.csv",
        ),
        source="okiden.co.jp",
    ),
}

# ─── Legacy area archive configs ─────────────────────────────────────────────
# The legacy CSVs differ wildly per TSO (annual/quarterly/monthly files; combined
# vs split DATE/TIME; multi-row and multi-line-quoted headers; unit suffixes;
# ambiguous duplicated 実績/抑制量 sub-columns). Rather than fight the column
# names, we map by COLUMN INDEX (stable per TSO across years, verified) and find
# the first data row dynamically. column_map: {col_index: (mode, "production"|"storage")}.
# Combined thermal (火力 / 火力等) maps to "unknown" — it cannot be split.


@dataclass(frozen=True)
class _LegacyAreaConfig:
    url_builder: Callable[[datetime], str]
    source: str
    column_map: dict[int, tuple[str, str]]
    datetime_combined: bool = False  # True: one "YYYY/M/D H:MM" column at index 0
    kanji_time: bool = False  # True: TIME column is "N時" (JP-HKD)
    unit_multiplier: float = 1.0  # JP-TK is in 万kWh (×10 → MWh ≈ MW at 1h)
    referer: str | None = None  # JP-KN requires a Referer header


def _hr_legacy_url(dt: datetime) -> str:
    """Hokuriku: monthly from 2018-10, calendar-quarter-grouped before that."""
    base = "https://www.rikuden.co.jp/nw_jyukyudata/attach/area_jisseki_rikuden"
    if dt >= datetime(2018, 10, 1, tzinfo=ZONE_INFO):
        if dt.strftime("%Y%m") == "201910":
            # One-off revised filename on Rikuden's archive page.
            return f"{base}201910_01.csv"
        return f"{base}{dt.strftime('%Y%m')}.csv"
    q_start = ((dt.month - 1) // 3) * 3 + 1
    return f"{base}{dt.year}{q_start:02d}_{q_start + 2:02d}.csv"


# Split DATE/TIME layout shared by HKD, TK, CB, HR, CG (demand at 2, fuels 3-13).
_LEGACY_MAP_SPLIT_STANDARD: dict[int, tuple[str, str]] = {
    3: ("nuclear", "production"),
    4: ("unknown", "production"),  # 火力 (combined thermal)
    5: ("hydro", "production"),
    6: ("geothermal", "production"),
    7: ("biomass", "production"),
    8: ("solar", "production"),
    10: ("wind", "production"),
    12: ("hydro", "storage"),  # 揚水 (pumped)
}

_LEGACY_AREA_CONFIGS: dict[str, _LegacyAreaConfig] = {
    "JP-HKD": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://www.hepco.co.jp/network/con_service/public_document/"
            f"supply_demand_results/csv/sup_dem_results_{_fiscal_year(dt)}_{_fiscal_quarter(dt)}q.csv"
        ),
        source="hepco.co.jp",
        column_map=_LEGACY_MAP_SPLIT_STANDARD,
        kanji_time=True,
    ),
    "JP-TH": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://setsuden.nw.tohoku-epco.co.jp/common/demand/"
            f"juyo_{_fiscal_year(dt)}_tohoku_{_fiscal_quarter(dt)}Q.csv"
        ),
        source="setsuden.nw.tohoku-epco.co.jp",
        # Tohoku column order differs (hydro/thermal/nuclear before solar).
        column_map={
            2: ("hydro", "production"),
            3: ("unknown", "production"),
            4: ("nuclear", "production"),
            5: ("solar", "production"),
            7: ("wind", "production"),
            9: ("geothermal", "production"),
            10: ("biomass", "production"),
            11: ("hydro", "storage"),
        },
        datetime_combined=True,
    ),
    "JP-TK": _LegacyAreaConfig(
        url_builder=lambda dt: (
            f"https://www.tepco.co.jp/forecast/html/images/area-{_fiscal_year(dt)}.csv"
        ),
        source="tepco.co.jp",
        column_map=_LEGACY_MAP_SPLIT_STANDARD,
        unit_multiplier=10.0,  # 万kWh → MWh
    ),
    "JP-CB": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://powergrid.chuden.co.jp/denki_yoho_content_data/"
            f"{_fiscal_year(dt)}_areabalance_current_term.csv"
        ),
        source="powergrid.chuden.co.jp",
        column_map=_LEGACY_MAP_SPLIT_STANDARD,
    ),
    "JP-HR": _LegacyAreaConfig(
        url_builder=_hr_legacy_url,
        source="rikuden.co.jp",
        column_map=_LEGACY_MAP_SPLIT_STANDARD,
    ),
    "JP-KN": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://www.kansai-td.co.jp/denkiyoho/area-performance/csv/"
            f"area_jyukyu_jisseki_{_fiscal_year(dt)}.csv"
        ),
        source="kansai-td.co.jp",
        # Combined DATE_TIME; demand at 1, fuels 2-12.
        column_map={
            2: ("nuclear", "production"),
            3: ("unknown", "production"),
            4: ("hydro", "production"),
            5: ("geothermal", "production"),
            6: ("biomass", "production"),
            7: ("solar", "production"),
            9: ("wind", "production"),
            11: ("hydro", "storage"),
        },
        datetime_combined=True,
        referer="https://www.kansai-td.co.jp/denkiyoho/area-performance/past.html",
    ),
    "JP-CG": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://www.energia.co.jp/nw/service/retailer/data/area/csv/"
            f"kako-{_fiscal_year(dt)}.csv"
        ),
        source="energia.co.jp",
        column_map=_LEGACY_MAP_SPLIT_STANDARD,
    ),
    "JP-KY": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://www.kyuden.co.jp/td_area_jukyu/csv_area_jyukyu_jisseki/"
            f"area_jyukyu_jisseki_{_fiscal_year(dt)}_{_fiscal_quarter(dt)}Q.csv"
        ),
        source="kyuden.co.jp",
        # Same combined layout as Kansai.
        column_map={
            2: ("nuclear", "production"),
            3: ("unknown", "production"),
            4: ("hydro", "production"),
            5: ("geothermal", "production"),
            6: ("biomass", "production"),
            7: ("solar", "production"),
            9: ("wind", "production"),
            11: ("hydro", "storage"),
        },
        datetime_combined=True,
    ),
    "JP-ON": _LegacyAreaConfig(
        url_builder=lambda dt: (
            "https://www.okiden.co.jp/business-support/service/"
            f"supply-and-demand/jukyu/csv/{_fiscal_year(dt)}.csv"
        ),
        source="okiden.co.jp",
        # Islanded grid: only thermal/hydro/biomass/solar/wind (no nuclear,
        # geothermal, pumped or interconnector). Index 3 is an empty spacer.
        column_map={
            4: ("unknown", "production"),
            5: ("hydro", "production"),
            6: ("biomass", "production"),
            7: ("solar", "production"),
            9: ("wind", "production"),
        },
    ),
}

# Column mapping: normalized Japanese column name → (mode_name, category).
# "production" fields go into ProductionMix, "storage" fields into StorageMix (negated).
# Columns not listed here are silently skipped (curtailment, 連系線, 合計, etc.).
_AREA_COLUMN_MAP: dict[str, tuple[str, str]] = {
    "原子力": ("nuclear", "production"),
    "火力(LNG)": ("gas", "production"),
    "火力(石炭)": ("coal", "production"),
    "火力(石油)": ("oil", "production"),
    "火力(その他)": ("unknown", "production"),
    "水力": ("hydro", "production"),
    "地熱": ("geothermal", "production"),
    "バイオマス": ("biomass", "production"),
    "太陽光発電実績": ("solar", "production"),
    "風力発電実績": ("wind", "production"),
    "その他": ("unknown", "production"),
    "揚水": ("hydro", "storage"),
    "蓄電池": ("battery", "storage"),
}


# ─── Area CSV helper functions ───────────────────────────────────────────────


def _read_area_csv(content: bytes) -> pd.DataFrame:
    """Read an area supply-demand CSV, handling encoding and format quirks.

    Handles: UTF-8 (JP-TK) vs Shift-JIS (others), full-width parens/alphabet
    (JP-KN, JP-KY), quoted values (JP-KY), and 20-col vs 22-col variants.
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("shift_jis")

    df = pd.read_csv(StringIO(text), header=1)
    # Normalize full-width chars: 火力（ＬＮＧ） → 火力(LNG)
    df.columns = [unicodedata.normalize("NFKC", str(col)).strip() for col in df.columns]
    return df


def _parse_area_datetime(date_val: Any, time_val: Any) -> datetime:
    """Parse DATE + TIME from area CSV into a tz-aware datetime.

    Handles: YYYY/MM/DD, YYYY/M/D, YYYYMMDD date formats; HH:MM and H:MM time
    formats with optional seconds (JP-ON files before ~2025-01-29 use
    H:MM:SS); the 24:00 edge case.
    """
    date_str = str(date_val).strip().strip('"')
    time_str = str(time_val).strip().strip('"')

    extra_day = False
    if "24:00" in time_str:
        time_str = "00:00"
        extra_day = True

    combined = f"{date_str} {time_str}"
    for fmt in (
        "%Y/%m/%d %H:%M",
        "%Y%m%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y%m%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(combined, fmt)
            if extra_day:
                dt += timedelta(days=1)
            return dt.replace(tzinfo=ZONE_INFO)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse area CSV datetime: {combined!r}")


def _df_to_production_breakdown_list(
    df: pd.DataFrame,
    zone_key: str,
    source: str,
    target_date: datetime,
    logger: Logger,
    datetime_offset: timedelta = timedelta(),
) -> list:
    """Convert area CSV DataFrame rows for target_date into production events."""
    production_list = ProductionBreakdownList(logger)

    def _safe_datetime(row) -> datetime | None:
        # The current month's file pads future slots with blank DATE/TIME
        # (JP-HKD); skip those. A NON-blank value that fails to parse means
        # the TSO changed format (JP-ON added/dropped seconds) — fail loud
        # rather than silently returning an empty day.
        if pd.isna(row["DATE"]) or pd.isna(row["TIME"]):
            return None
        return _parse_area_datetime(row["DATE"], row["TIME"]) + datetime_offset

    df = df.copy()
    df["_datetime"] = df.apply(_safe_datetime, axis=1)
    df = df[df["_datetime"].notna()]

    # Filter to target date only
    target_day = target_date.date()
    df = df[df["_datetime"].apply(lambda dt: dt.date() == target_day)]

    if df.empty:
        return production_list.to_list()

    # Build per-row lookup: which CSV columns map to which mode
    col_targets: list[tuple[str, str, str]] = []  # (csv_col, field, category)
    for col in df.columns:
        if col in _AREA_COLUMN_MAP:
            field, category = _AREA_COLUMN_MAP[col]
            col_targets.append((col, field, category))

    for _, row in df.iterrows():
        prod_values: dict[str, float] = {}
        storage_values: dict[str, float] = {}

        for csv_col, field, category in col_targets:
            val = row[csv_col]
            if pd.isna(val):
                continue
            try:
                val = float(val)
            except (TypeError, ValueError):
                continue  # stray placeholder text in a numeric column

            if category == "production":
                # Accumulate (火力(その他) and その他 both map to "unknown")
                prod_values[field] = prod_values.get(field, 0.0) + val
            elif category == "storage":
                # CSV: positive = generating, negative = pumping
                # EM:  positive = charging,   negative = discharging
                storage_values[field] = -val

        # Future slots in the current month's file have a timestamp but no
        # values; appending them would only log a validation error.
        if not prod_values and not storage_values:
            continue

        production_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=row["_datetime"],
            source=source,
            production=ProductionMix(**prod_values),
            storage=StorageMix(**storage_values) if storage_values else None,
        )

    return production_list.to_list()


def _fetch_area_csv_content(
    config: _AreaCsvConfig, target_datetime: datetime, session: Session
) -> bytes:
    """Return the raw CSV bytes for target_datetime's month.

    Tries the monthly URL, then falls back to the fiscal-year ZIP (zones that
    archive older months, e.g. JP-CB) or the per-day realtime file (zones that
    publish the monthly file late, e.g. JP-TH).
    """
    response = session.get(
        config.url_builder(target_datetime), headers=_REQUEST_HEADERS
    )
    if response.status_code == 404:
        if config.zip_url_builder is not None and config.zip_member_builder is not None:
            zip_response = session.get(
                config.zip_url_builder(target_datetime), headers=_REQUEST_HEADERS
            )
            zip_response.raise_for_status()
            with ZipFile(BytesIO(zip_response.content)) as archive:
                return archive.read(config.zip_member_builder(target_datetime))
        if config.daily_url_builder is not None:
            daily_response = session.get(
                config.daily_url_builder(target_datetime), headers=_REQUEST_HEADERS
            )
            daily_response.raise_for_status()
            return daily_response.content
    response.raise_for_status()
    return response.content


def _fetch_production_area_csv(
    zone_key: str,
    target_datetime: datetime,
    session: Session | None,
    logger: Logger,
) -> list:
    """Fetch and parse the area supply-demand CSV for a zone."""
    config = _AREA_CSV_CONFIGS[zone_key]
    session = session or Session()
    content = _fetch_area_csv_content(config, target_datetime, session)
    df = _read_area_csv(content)
    return _df_to_production_breakdown_list(
        df,
        zone_key,
        config.source,
        target_datetime,
        logger,
        datetime_offset=config.datetime_offset,
    )


# ─── Legacy area archive helpers ─────────────────────────────────────────────

_LEGACY_MAX_COLS = 20
_LEGACY_DATE_RE = re.compile(r"^\s*\d{4}/\d{1,2}/\d{1,2}")
_LEGACY_MISSING = {"", "-", "−", "ー", "―", "—", "nan"}


def _read_legacy_area_csv(content: bytes) -> pd.DataFrame:
    """Read a legacy archive as raw positional strings.

    Uses a fixed column count so ragged preamble rows don't break parsing, and
    lets pandas handle quoted fields (including the multi-line quoted headers in
    JP-ON). Header detection happens later by locating the first dated row.
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("shift_jis")
    # With names=range(N), pandas would silently demote leftmost extra columns
    # to the index on wider rows, shifting every positional mapping — fail loud.
    widest = max(len(fields) for fields in csv.reader(StringIO(text)))
    if widest > _LEGACY_MAX_COLS:
        raise ValueError(
            f"Legacy area CSV has {widest} columns (> {_LEGACY_MAX_COLS}); "
            "positional column_map would be misaligned"
        )
    return pd.read_csv(
        StringIO(text),
        header=None,
        names=range(_LEGACY_MAX_COLS),
        dtype=object,
        keep_default_na=False,
        skip_blank_lines=False,
    )


def _legacy_value_to_float(value: Any) -> float | None:
    """Parse a legacy cell; treat blanks and lone dashes as missing.

    Normalizes full-width digits/signs (NFKC) and the Unicode minus (U+2212,
    untouched by NFKC) so signed pumped-storage values aren't silently dropped.
    """
    text = str(value).strip().strip('"')
    if text in _LEGACY_MISSING:
        return None
    text = unicodedata.normalize("NFKC", text).replace("−", "-")
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def _build_legacy_datetime(date_str: str, time_str: str, kanji_time: bool) -> datetime:
    """Combine a YYYY/M/D date with an hourly time ('H:MM' or 'N時')."""
    if kanji_time:
        hour, minute = int(time_str.replace("時", "").strip()), 0
    else:
        hh, _, mm = time_str.partition(":")
        hour, minute = int(hh), int(mm) if mm.strip() else 0
    day = datetime.strptime(date_str.strip(), "%Y/%m/%d")
    return day.replace(hour=hour, minute=minute, tzinfo=ZONE_INFO)


def _legacy_df_to_breakdown(
    df: pd.DataFrame,
    config: _LegacyAreaConfig,
    zone_key: str,
    target_datetime: datetime,
    logger: Logger,
) -> list:
    """Convert a legacy archive DataFrame's rows for target_datetime's day."""
    production_list = ProductionBreakdownList(logger)
    target_day = target_datetime.date()
    rows = df.values.tolist()

    # Find the first data row (column 0 looks like a date); skips all header rows.
    start = next(
        (
            i
            for i, row in enumerate(rows)
            if _LEGACY_DATE_RE.match(str(row[0]).strip().strip('"'))
        ),
        None,
    )
    if start is None:
        return production_list.to_list()

    last_date: str | None = None
    for row in rows[start:]:
        cell0 = str(row[0]).strip().strip('"')
        if config.datetime_combined:
            parts = cell0.split()
            if len(parts) != 2:
                continue
            date_str, time_str = parts
        else:
            # Split DATE/TIME: date is written once per day, so carry it forward.
            if _LEGACY_DATE_RE.match(cell0):
                last_date = cell0
            time_str = str(row[1]).strip().strip('"')
            if last_date is None or time_str in _LEGACY_MISSING:
                continue
            date_str = last_date

        try:
            dt = _build_legacy_datetime(date_str, time_str, config.kanji_time)
        except (ValueError, TypeError):
            continue
        if dt.date() != target_day:
            continue

        prod: dict[str, float] = {}
        storage: dict[str, float] = {}
        for idx, (mode, category) in config.column_map.items():
            value = _legacy_value_to_float(row[idx])
            if value is None:
                continue
            value *= config.unit_multiplier
            if category == "production":
                prod[mode] = prod.get(mode, 0.0) + value
            else:
                storage[mode] = -value

        production_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=dt,
            source=config.source,
            production=ProductionMix(**prod),
            storage=StorageMix(**storage) if storage else None,
        )
    return production_list.to_list()


# Legacy archives are immutable historical files that cover a quarter or a
# whole fiscal year, but the parser is invoked one day at a time — without a
# cache a year of backfill would re-download the same annual file ~365 times.
_LEGACY_CSV_CACHE: dict[str, bytes] = {}
_LEGACY_CSV_CACHE_MAX = 4


def _fetch_production_legacy_area_csv(
    zone_key: str,
    target_datetime: datetime,
    session: Session | None,
    logger: Logger,
) -> list:
    """Fetch and parse a pre-new-format legacy area archive (hourly, ~2016+)."""
    config = _LEGACY_AREA_CONFIGS[zone_key]
    session = session or Session()
    url = config.url_builder(target_datetime)
    content = _LEGACY_CSV_CACHE.get(url)
    if content is None:
        headers = dict(_REQUEST_HEADERS)
        if config.referer:
            headers["Referer"] = config.referer
        response = session.get(url, headers=headers)
        response.raise_for_status()
        content = response.content
        while len(_LEGACY_CSV_CACHE) >= _LEGACY_CSV_CACHE_MAX:
            _LEGACY_CSV_CACHE.pop(next(iter(_LEGACY_CSV_CACHE)))
        _LEGACY_CSV_CACHE[url] = content
    df = _read_legacy_area_csv(content)
    return _legacy_df_to_breakdown(df, config, zone_key, target_datetime, logger)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Fetch the production mix from the TSO area supply-demand CSVs.

    Routing by date:
      * on/after _AREA_CSV_START_DATES → new 30-min format (full breakdown).
      * earlier, on/after _LEGACY_AREA_START_DATES → legacy hourly archive
        (combined thermal as "unknown", no battery).
      * earlier still (or unsupported zone, e.g. JP-SK pre-2024-03) → raise.
    """
    dt = (
        target_datetime.astimezone(ZONE_INFO)
        if target_datetime is not None
        else datetime.now(ZONE_INFO)
    )

    new_start = _AREA_CSV_START_DATES.get(zone_key)
    if new_start is not None and dt >= new_start and zone_key in _AREA_CSV_CONFIGS:
        return _fetch_production_area_csv(zone_key, dt, session, logger)

    legacy_start = _LEGACY_AREA_START_DATES.get(zone_key)
    if (
        legacy_start is not None
        and dt >= legacy_start
        and zone_key in _LEGACY_AREA_CONFIGS
    ):
        return _fetch_production_legacy_area_csv(zone_key, dt, session, logger)

    raise NotImplementedError(
        f"No area supply-demand data available for {zone_key} at {dt.date()}"
    )


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO) + timedelta(days=1)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    # price files contain data for fiscal year and not calendar year.
    if target_datetime.month <= 3:
        fiscal_year = target_datetime.year - 1
    else:
        fiscal_year = target_datetime.year
    url = f"http://www.jepx.jp/market/excel/spot_{fiscal_year}.csv"
    df = pd.read_csv(url, encoding="shift-jis")

    df = df.iloc[:, [0, 1, 6, 7, 8, 9, 10, 11, 12, 13, 14]]
    df.columns = [
        "Date",
        "Period",
        "JP-HKD",
        "JP-TH",
        "JP-TK",
        "JP-CB",
        "JP-HR",
        "JP-KN",
        "JP-CG",
        "JP-SK",
        "JP-KY",
    ]

    if zone_key not in df.columns[2:]:
        return []

    start = target_datetime - timedelta(days=1)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y/%m/%d").dt.date
    df = df[(df["Date"] >= start.date()) & (df["Date"] <= target_datetime.date())]

    df["datetime"] = df.apply(
        lambda row: (
            datetime.combine(row["Date"], datetime.min.time()).replace(tzinfo=ZONE_INFO)
            + timedelta(minutes=30 * (row["Period"] - 1))
        ),
        axis=1,
    )

    data = []
    for row in df.iterrows():
        data.append(
            {
                "zoneKey": zone_key,
                "currency": "JPY",
                "datetime": row[1]["datetime"].to_pydatetime(),
                "price": round(
                    int(1000 * row[1][zone_key]), -1
                ),  # Convert from JPY/kWh to JPY/MWh
                "source": "jepx.jp",
            }
        )

    return data


SOURCES_FORECAST_DATA = {
    "JP-HKD": "denkiyoho.hepco.co.jp",
    "JP-TH": "setsuden.nw.tohoku-epco.co.jp",
    "JP-TK": "www.tepco.co.jp/forecast",
    "JP-CB": "powergrid.chuden.co.jp",
    "JP-HR": "www.rikuden.co.jp/nw/denki-yoho",
    "JP-KN": "www.kansai-td.co.jp",
    "JP-SK": "www.yonden.co.jp",
    "JP-CG": "www.energia.co.jp",
    "JP-KY": "www.kyuden.co.jp",
    "JP-ON": "www.okiden.co.jp/denki2/",
}


def read_csv_forecast(
    datestamp, zone_key, session, logger, data_type=None
):  # data_type = generation_fcst or consumption_fcst
    """Reads the file where the forecast data is given, for a given zone in Japan. Now implemented for consumption and generation forecast data."""
    if datestamp < datetime.now(ZONE_INFO).strftime("%Y%m%d"):
        raise NotImplementedError("Past dates not implemented for selected region")

    # Forecasts ahead of current date are not available for JP-KY
    if datestamp > datetime.now(ZONE_INFO).strftime("%Y%m%d") and zone_key == "JP-KY":
        raise NotImplementedError(
            "Future dates (local time) not implemented for selected region"
        )

    # Forecasts ahead of tomorrow's date are not available
    if datestamp > (datetime.now(ZONE_INFO) + timedelta(days=1)).strftime("%Y%m%d"):
        raise NotImplementedError(
            "Dates after tomorrow (local time) not implemented for selected region"
        )

    # Urls for some Japan zones based on datestamp
    forecast_url = {
        "JP-HKD": f"http://denkiyoho.hepco.co.jp/area/data/{datestamp}_hokkaido_yosoku.csv",
        "JP-HR": f"https://www.rikuden.co.jp/nw/denki-yoho/csv/yosoku_05_{datestamp}.csv",
        "JP-KN": f"https://www.kansai-td.co.jp/interchange/denkiyoho/imbalance/{datestamp}_yosoku.csv",
        "JP-CG": f"https://www.energia.co.jp/nw/jukyuu/sys/{datestamp[:6]}_jyukyu2_chugoku.zip",
        "JP-KY": rf"https://www.kyuden.co.jp/td_power_usages/csv/kouhyo/imbalance/21110_TSO9_0_{datestamp}.csv?a={datestamp}\d{6}",
        "JP-ON": f"http://www.okiden.co.jp/denki2/dem_pg/csv/jukyu_yosoku_{datestamp}.csv",
    }

    # For zones with different URLs for today vs tomorrow
    if datestamp == datetime.now(ZONE_INFO).strftime("%Y%m%d"):
        forecast_url["JP-TH"] = (
            f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_{datestamp}.csv"
        )
        forecast_url["JP-TK"] = (
            "https://www4.tepco.co.jp/forecast/html/images/AREA_YOSOKU.csv"
        )
        forecast_url["JP-CB"] = (
            "https://powergrid.chuden.co.jp/denki_yoho_content_data/keito_yosoku_cepco003.csv"
        )
        forecast_url["JP-SK"] = (
            "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_today.csv"
        )
    # TODO: what time the new doc is created for next day?
    elif datestamp == (datetime.now(ZONE_INFO) + timedelta(days=1)).strftime("%Y%m%d"):
        forecast_url["JP-TH"] = (
            "https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_y.csv"
        )
        forecast_url["JP-TK"] = (
            "https://www4.tepco.co.jp/forecast/html/images/AREA_ONCE_YOSOKU.csv"
        )
        forecast_url["JP-SK"] = (
            "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_tomorrow.csv"
        )
        if zone_key == "JP-CB":  # Raise exception for JP-CB
            raise ValueError(
                f"Forecast data for tomorrow not available for zone: {zone_key}"
            )

    # Skip non-tabular data at the start of source files
    startrow = 1 if zone_key == "JP-HR" else 3 if zone_key == "JP-KN" else 2

    # Get response from correspondent url
    response = session.get(forecast_url[zone_key])

    # Parse the different formats
    df = pd.DataFrame()
    if zone_key == "JP-CG":
        with ZipFile(BytesIO(response.content)) as z:
            target_file = f"{datestamp}_yosoku_chugoku.csv"
            if target_file in z.namelist():
                with z.open(target_file) as f:
                    df = pd.read_csv(f, encoding="shift_jis", skiprows=startrow)
            else:
                logger.error(f"File '{target_file}' not found in the zip archive.")
                logger.debug(f"Available files: {z.namelist()}")
    else:
        content = response.content.decode("shift_jis")
        df = pd.read_csv(StringIO(content), skiprows=startrow)

    # Check if df is still empty after the above operations
    if df.empty:
        logger.error(f"Failed to load forecast data for {zone_key}")
        raise ValueError(f"Could not obtain forecast data for zone: {zone_key}")

    # Consumption or generation data
    if data_type == "consumption_fcst":
        column_name_japanese = "エリア総需要量"
    elif data_type == "generation_fcst":
        column_name_japanese = "エリア総発電量"

    # Extract the correspondant information from the files for each zone
    if zone_key == "JP-HKD" or zone_key == "JP-HR":
        df = df[["日付", "時間帯_自", column_name_japanese + "(kWh)"]]
    elif zone_key == "JP-KN" or zone_key == "JP-KY":
        if zone_key == "JP-KY":
            df = df.drop(index=0)
        df = df[["日付", "時間帯＿自", column_name_japanese]]
    elif zone_key == "JP-CG" or zone_key == "JP-CB" or zone_key == "JP-SK":
        df = df[["日付", "時間帯_自", column_name_japanese]]
    elif zone_key == "JP-ON" or zone_key == "JP-TH":
        df = df[["DATE", "時間帯_自", column_name_japanese + "(kWh)"]]
    elif zone_key == "JP-TK":
        df = df[
            ["日付(yyyymmdd)", "時間帯_自(HH:MI)", column_name_japanese + "[30分kWh]"]
        ]

    df.columns = ["Date", "Time", data_type]

    return df


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZoneKey("JP-HKD"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Gets demand/consumption forecast for every half hour for the specified Japan zones in MW."""
    # Session
    session = session or Session()

    # Date
    # Currently past dates not implemented for areas with no date in their demand csv files
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    datestamp = target_datetime.astimezone(ZONE_INFO).strftime("%Y%m%d")

    # Read csv
    df = read_csv_forecast(
        datestamp, zone_key, session, logger, data_type="consumption_fcst"
    )

    # Transform to MW: the data is given every half hour
    df["consumption_fcst"] = df["consumption_fcst"].astype(float) * 2 / 1000

    all_consumption_events = df  # all events with a datetime and a consumption value
    consumption_list = TotalConsumptionList(logger)

    for row in all_consumption_events.itertuples():
        if (
            zone_key == "JP-HR"
            or zone_key == "JP-ON"
            or zone_key == "JP-TH"
            or zone_key == "JP-CB"
        ):
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y/%m/%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-TK":
            # Format as string in the format "YYYYMMDD HHMM" and parse
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time:04d}", "%Y%m%d %H%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-KY":
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        else:
            # Use strptime to directly parse the date integer and time string
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)

        consumption_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            consumption=row.consumption_fcst,
            source=SOURCES_FORECAST_DATA[zone_key],
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


def fetch_generation_forecast(
    zone_key: ZoneKey = ZoneKey("JP-HKD"),  # Just as default
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Gets generation forecast for every half hour for the specified Japan zones in MW."""

    # Session
    session = session or Session()

    # Date
    # Currently past dates not implemented for areas with no date in their demand csv files
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    datestamp = target_datetime.astimezone(ZONE_INFO).strftime("%Y%m%d")

    # Read csv
    df = read_csv_forecast(
        datestamp, zone_key, session, logger, data_type="generation_fcst"
    )

    # Transform to MW: the data is given every half hour
    df["generation_fcst"] = df["generation_fcst"].astype(float) * 2 / 1000

    all_generation_events = df  # all events with a datetime and a generation value
    generation_list = TotalProductionList(logger)

    for row in all_generation_events.itertuples():
        if (
            zone_key == "JP-HR"
            or zone_key == "JP-ON"
            or zone_key == "JP-TH"
            or zone_key == "JP-CB"
        ):
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y/%m/%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-TK":
            # Format as string in the format "YYYYMMDD HHMM" and parse
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time:04d}", "%Y%m%d %H%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-KY":
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        else:
            # Use strptime to directly parse the date integer and time string
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)

        generation_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            value=row.generation_fcst,
            source=SOURCES_FORECAST_DATA[zone_key],
            sourceType=EventSourceType.forecasted,
        )
    return generation_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    """
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    """
    print("fetch_consumption_forecast() ->")
    print(fetch_consumption_forecast())
    print("fetch_consumption_forecast(JP-TH) ->")
    print(fetch_consumption_forecast("JP-TH"))
    print("fetch_consumption_forecast(JP-TK) ->")
    print(fetch_consumption_forecast("JP-TK"))
    print("fetch_consumption_forecast(JP-CB) ->")
    print(fetch_consumption_forecast("JP-CB"))
    print("fetch_consumption_forecast(JP-KN) ->")
    print(fetch_consumption_forecast("JP-KN"))
    print("fetch_consumption_forecast(JP-SK) ->")
    print(fetch_consumption_forecast("JP-SK"))
    print("fetch_consumption_forecast(JP-KY) ->")
    print(fetch_consumption_forecast("JP-KY"))
    print("fetch_consumption_forecast(JP-ON) ->")
    print(fetch_consumption_forecast("JP-ON"))

    print(
        fetch_generation_forecast(
            zone_key="JP-HKD", target_datetime=datetime(2025, 4, 25)
        )
    )

    print(
        fetch_consumption_forecast(
            zone_key="JP-HKD", target_datetime=datetime(2025, 4, 25)
        )
    )
