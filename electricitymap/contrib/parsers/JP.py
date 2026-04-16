#!/usr/bin/env python3
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

from electricitymap.contrib.config import ZONES_CONFIG
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
from electricitymap.contrib.parsers import occtonet
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

sources = {
    "JP-HKD": "denkiyoho.hepco.co.jp",
    "JP-TH": "setsuden.nw.tohoku-epco.co.jp",
    "JP-TK": "www.tepco.co.jp",
    "JP-CB": "denki-yoho.chuden.jp",
    "JP-HR": "www.rikuden.co.jp/denki-yoho",
    "JP-KN": "www.kepco.co.jp",
    "JP-SK": "www.yonden.co.jp",
    "JP-CG": "www.energia.co.jp",
    "JP-KY": "www.kyuden.co.jp/power_usages/pc.html",
    "JP-ON": "www.okiden.co.jp/denki/",
}
ZONES_ONLY_LIVE = ["JP-TK", "JP-CB", "JP-SK"]
ZONE_INFO = ZoneInfo("Asia/Tokyo")

# ─── Area CSV: per-zone date cutoff ──────────────────────────────────────────
# For dates on or after the cutoff, use the new area-CSV parser.
# For dates before (or zones not listed), use the legacy consumption-based parser.
# Adjust per zone as data coverage depth is verified.
_AREA_CSV_START_DATES: dict[str, datetime] = {
    # Uncomment zones as they are validated:
    # "JP-HKD": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-TH": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-TK": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-HR": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-KN": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-CG": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-SK": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-KY": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
    # "JP-ON": datetime(2024, 4, 1, tzinfo=ZONE_INFO),
}


@dataclass(frozen=True)
class _AreaCsvConfig:
    url_builder: Callable[[datetime], str]
    source: str
    fallback_url_builder: Callable[[datetime], str] | None = None


def _monthly(base: str, suffix: str) -> Callable[[datetime], str]:
    """Standard monthly URL pattern: base + YYYYMM + suffix."""
    return lambda dt: f"{base}{dt.strftime('%Y%m')}{suffix}"


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
            "https://nw.tohoku-epco.co.jp/common/demand/eria_jukyu_", "_02.csv"
        ),
        source="nw.tohoku-epco.co.jp",
    ),
    "JP-TK": _AreaCsvConfig(
        url_builder=_monthly(
            "https://www.tepco.co.jp/forecast/html/images/eria_jukyu_", "_03.csv"
        ),
        source="tepco.co.jp",
    ),
    # JP-CB: URL to be discovered during implementation
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

    Handles: YYYY/MM/DD, YYYY/M/D, YYYYMMDD date formats;
    HH:MM and H:MM time formats; the 24:00 edge case.
    """
    date_str = str(date_val).strip().strip('"')
    time_str = str(time_val).strip().strip('"')

    extra_day = False
    if "24:00" in time_str:
        time_str = "00:00"
        extra_day = True

    combined = f"{date_str} {time_str}"
    for fmt in ("%Y/%m/%d %H:%M", "%Y%m%d %H:%M"):
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
) -> list:
    """Convert area CSV DataFrame rows for target_date into production events."""
    production_list = ProductionBreakdownList(logger)

    df = df.copy()
    df["_datetime"] = df.apply(
        lambda r: _parse_area_datetime(r["DATE"], r["TIME"]), axis=1
    )

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
            val = float(val)

            if category == "production":
                # Accumulate (火力(その他) and その他 both map to "unknown")
                prod_values[field] = prod_values.get(field, 0.0) + val
            elif category == "storage":
                # CSV: positive = generating, negative = pumping
                # EM:  positive = charging,   negative = discharging
                storage_values[field] = -val

        production_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=row["_datetime"],
            source=source,
            production=ProductionMix(**prod_values),
            storage=StorageMix(**storage_values) if storage_values else None,
        )

    return production_list.to_list()


def _fetch_production_area_csv(
    zone_key: str,
    target_datetime: datetime,
    session: Session | None,
    logger: Logger,
) -> list:
    """Fetch and parse the area supply-demand CSV for a zone."""
    config = _AREA_CSV_CONFIGS[zone_key]
    session = session or Session()
    response = session.get(config.url_builder(target_datetime))
    if response.status_code == 404 and config.fallback_url_builder:
        response = session.get(config.fallback_url_builder(target_datetime))
    response.raise_for_status()
    df = _read_area_csv(response.content)
    return _df_to_production_breakdown_list(
        df, zone_key, config.source, target_datetime, logger
    )


# ─── Legacy helpers (unchanged) ──────────────────────────────────────────────


def get_wind_capacity(datetime: datetime, zone_key, logger: Logger):
    ZONE_CONFIG = ZONES_CONFIG[zone_key]
    try:
        capacity = ZONE_CONFIG["capacity"]["wind"]
        if zone_key == "JP-HKD":
            if datetime.year <= 2019:
                capacity = 480
            elif datetime.year == 2020:
                capacity = 520
            elif datetime.year >= 2021:
                capacity = 577
    except Exception as e:
        logger.error(f"Wind capacity not found in configuration file: {e.args}")
        capacity = None
    return capacity


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Routes between the new area-CSV parser and the legacy consumption-based parser.

    The routing is controlled by _AREA_CSV_START_DATES: for dates on or after
    the per-zone cutoff the area CSV is used (full mode breakdown); for earlier
    dates the legacy all-unknown path is used.
    """
    if target_datetime is not None:
        dt = target_datetime.astimezone(ZONE_INFO)
    else:
        dt = datetime.now(ZONE_INFO)

    start_date = _AREA_CSV_START_DATES.get(zone_key)
    if (
        start_date is not None
        and dt >= start_date
        and zone_key in _AREA_CSV_CONFIGS
    ):
        return _fetch_production_area_csv(zone_key, dt, session, logger)
    return _fetch_production_consumption_based(
        zone_key, session, target_datetime, logger
    )


def _fetch_production_consumption_based(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Legacy path: calculates production from consumption minus imports.

    All production is mapped to unknown (plus solar where available).
    """
    df = fetch_production_df(zone_key, session, target_datetime)
    # add a row to production for each entry in the dictionary:

    datalist = []

    for i in df.index:
        capacity = get_wind_capacity(
            df.loc[i, "datetime"].to_pydatetime(), zone_key, logger
        )
        data = {
            "zoneKey": zone_key,
            "datetime": df.loc[i, "datetime"].to_pydatetime(),
            "production": {
                "biomass": None,
                "coal": None,
                "gas": None,
                "hydro": None,
                "nuclear": None,
                "oil": None,
                "solar": df.loc[i, "solar"] if "solar" in df.columns else None,
                "wind": None,
                "geothermal": None,
                "unknown": df.loc[i, "unknown"],
            },
            "capacity": {"wind": capacity if capacity is not None else {}},
            "source": f"occto.or.jp, {sources[zone_key]}",
        }
        datalist.append(data)
    return datalist


def fetch_production_df(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """
    Calculates production from consumption and imports for a given area.
    All production is mapped to unknown.
    """
    exch_map = {
        "JP-HKD": ["JP-TH"],
        "JP-TH": ["JP-TK", "JP-HKD"],
        "JP-TK": ["JP-TH", "JP-CB"],
        "JP-CB": ["JP-TK", "JP-HR", "JP-KN"],
        "JP-HR": ["JP-CB", "JP-KN"],
        "JP-KN": ["JP-CB", "JP-HR", "JP-SK", "JP-CG"],
        "JP-SK": ["JP-KN", "JP-CG"],
        "JP-CG": ["JP-KN", "JP-SK", "JP-KY"],
        "JP-ON": [],
        "JP-KY": ["JP-CG"],
    }
    df = fetch_consumption_df(zone_key, target_datetime)
    df["imports"] = 0
    for zone in exch_map[zone_key]:
        df2 = occtonet.fetch_exchange(
            zone_key1=zone_key,
            zone_key2=zone,
            session=session,
            target_datetime=target_datetime,
        )
        df2 = pd.DataFrame(df2)
        exchname = df2.loc[0, "sortedZoneKeys"]
        df2 = df2[["datetime", "netFlow"]]
        df2.columns = ["datetime", exchname]
        df = pd.merge(df, df2, how="inner", on="datetime")
        if exchname.split("->")[-1] == zone_key:
            df["imports"] = df["imports"] + df[exchname]
        else:
            df["imports"] = df["imports"] - df[exchname]
    # By default all production is mapped to unknown
    df["unknown"] = df["cons"] - df["imports"]
    # When there is solar, remove it from other production
    if "solar" in df.columns:
        df["unknown"] = df["unknown"] - df["solar"]
    return df


def fetch_consumption_df(
    zone_key: str = "JP-TK",
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """
    Returns the consumption for an area as a pandas DataFrame.
    For JP-CB the consumption file includes solar production.
    """
    if target_datetime is not None and zone_key in ZONES_ONLY_LIVE:
        raise NotImplementedError("This parser can only fetch live data")
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    datestamp = target_datetime.astimezone(ZONE_INFO).strftime("%Y%m%d")
    consumption_url = {
        "JP-HKD": f"http://denkiyoho.hepco.co.jp/area/data/juyo_01_{datestamp}.csv",
        "JP-TH": f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/juyo_02_{datestamp}.csv",
        "JP-TK": "https://www.tepco.co.jp/forecast/html/images/juyo-d1-j.csv",
        "JP-HR": f"http://www.rikuden.co.jp/nw/denki-yoho/csv/juyo_05_{datestamp}.csv",
        "JP-CB": "https://powergrid.chuden.co.jp/denki_yoho_content_data/juyo_cepco003.csv",
        "JP-KN": "https://www.kansai-td.co.jp/yamasou/juyo1_kansai.csv",
        "JP-CG": f"https://www.energia.co.jp/nw/jukyuu/sys/juyo_07_{datestamp}.csv",
        "JP-SK": "http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv",
        "JP-KY": f"https://www.kyuden.co.jp/td_power_usages/csv/juyo-hourly-{datestamp}.csv",
        "JP-ON": f"https://www.okiden.co.jp/denki2/juyo_10_{datestamp}.csv",
    }

    # First roughly 40 rows of the consumption files have hourly data,
    # the parser skips to the rows with 5-min actual values
    startrow = 57 if zone_key == "JP-KN" else 54

    try:
        df = pd.read_csv(
            consumption_url[zone_key], skiprows=startrow, encoding="shift-jis"
        )
    except pd.errors.EmptyDataError as e:
        logger.exception("Data not available yet")
        raise e

    if zone_key in ["JP-TH"]:
        df.columns = ["Date", "Time", "cons", "solar", "wind"]
    elif zone_key in ["JP-TK"]:
        df.columns = ["Date", "Time", "cons", "solar", "solar_pct"]
    else:
        df.columns = ["Date", "Time", "cons", "solar"]
    # Convert 万kW to MW
    df["cons"] = 10 * df["cons"]
    if "solar" in df.columns:
        df["solar"] = 10 * df["solar"]

    df = df.dropna()
    df["datetime"] = df.apply(parse_dt, axis=1)
    if "solar" in df.columns:
        df = df[["datetime", "cons", "solar"]]
    else:
        df = df[["datetime", "cons"]]
    return df


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


def parse_dt(row):
    """Parses datetime objects from date and time strings."""
    format_string = "%Y/%m/%d %H:%M"
    if "AM" in row["Time"] or "PM" in row["Time"]:
        format_string = "%Y/%m/%d %I:%M %p"
    datetime_string = " ".join([row["Date"], row["Time"]])
    return datetime.strptime(datetime_string, format_string).replace(tzinfo=ZONE_INFO)


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
