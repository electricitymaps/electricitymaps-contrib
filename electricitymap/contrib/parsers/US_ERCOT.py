"""Parser for the ERCOT grid area of the United States."""

import gzip
import json
import re
import time
import zipfile
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import lru_cache
from io import BytesIO
from logging import Logger, getLogger
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from requests import Response, Session

# import time
import electricitymap.contrib.parsers.EIA as EIA
from electricitymap.contrib.lib.models.event_lists import (
    LocationalMarginalPriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.utils import get_token
from electricitymap.contrib.parsers.lib.validation import validate_exchange
from electricitymap.contrib.types import ZoneKey

SOURCE = "ercot.com"
TX_TZ = ZoneInfo("US/Central")
US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAMETER = "host=https://www.ercot.com"

RT_GENERATION_URL = (
    f"{US_PROXY}/api/1/services/read/dashboards/fuel-mix.json?{HOST_PARAMETER}"
)
RT_CONSUMPTION_URL = f"{US_PROXY}/api/1/services/read/dashboards/loadForecastVsActual.json?{HOST_PARAMETER}"
RT_EXCHANGE_URL = (
    f"{US_PROXY}/api/1/services/read/dashboards/rtsyscond.json?{HOST_PARAMETER}"
)
RT_PRICES_URL = (
    f"{US_PROXY}/api/1/services/read/dashboards/systemWidePrices.json?{HOST_PARAMETER}"
)
RT_STORAGE_URL = f"{US_PROXY}/api/1/services/read/dashboards/energy-storage-resources.json?{HOST_PARAMETER}"
AUTH_URL_ERCOT = "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
DAYAHEAD_LMP_URL = f"{US_PROXY}/api/public-reports/np4-190-cd/dam_stlmnt_pnt_prices"
REALTIME_LMP_URL = f"{US_PROXY}/api/public-reports/np6-788-cd/lmp_node_zone_hub"

# Lists the yearly Fuel Mix Reports, whose links change every year
GENERATION_PAGE_URL = f"{US_PROXY}/gridinfo/generation?{HOST_PARAMETER}"
# The Fuel Mix Report has no storage category: battery discharge is reported in
# "Other" (no fuel type), and charging as "WSL" (Wholesale Storage Load) since 2022.
# Non-battery "Other" (petroleum coke, distillate oil) is ~3 MW on average, see #8935.
# Before 2022, "WSL" was netted into "Other", so it can't be told apart from oil.
BATTERY_IN_OTHER_SINCE = datetime(2022, 1, 1, tzinfo=TX_TZ)
FUEL_MIX_REPORT_FUELS = {
    "Biomass",
    "Coal",
    "Gas",
    "Gas-CC",
    "Hydro",
    "Nuclear",
    "Other",
    "Solar",
    "WSL",
    "Wind",
}
GENERATION_MAPPING = {
    "Coal and Lignite": "coal",
    "Hydro": "hydro",
    "Natural Gas": "gas",
    "Nuclear": "nuclear",
    "Other": "unknown",
    "Power Storage": "battery",
    # Since Oct 2026, the live fuel mix also splits "Power Storage" (net) into
    # these two keys. They are dropped in process_generation_dataframe: the net
    # value already covers them. Map them once we model charge/discharge modes.
    # "Power Storage Charging": ...,
    # "Power Storage Discharging": ...,
    "Solar": "solar",
    "Wind": "wind",
    "WSL": "battery",
    "Biomass": "biomass",
    "Gas": "gas",
    "Coal": "coal",
    "Gas-CC": "gas",
}
EXCHANGE_MAPPING = {"US-CENT-SWPP": ["dcE", "dcN"], "MX-NE": ["dcL"], "MX-NO": ["dcR"]}


# Report type IDs
class ReportTypeID(Enum):
    # Wind production actual and forecast: https://www.ercot.com/mp/data-products/data-product-details?id=NP4-732-CD
    WIND_POWER_PRODUCTION_REPORTID = 13028

    # Solar production forecast: https://www.ercot.com/mp/data-products/data-product-details?id=np4-737-cd
    SOLAR_POWER_PRODUCTION_REPORTID = 13483

    # Load forecast: https://www.ercot.com/mp/data-products/data-product-details?id=np3-560-cd
    LOAD_FORECAST_REPORTID = 12311


def get_data(
    url: str,
    session: Session | None = None,
    headers: dict | None = None,
    params: dict | None = None,
):
    """requests ERCOT url and return json"""
    if not session:
        session = Session()

    resp: Response = session.get(url, verify=False, headers=headers, params=params)
    response_text = gzip.decompress(resp.content).decode("utf-8")
    data_json = json.loads(response_text)
    return data_json


def parse_storage_data_live(session: Session) -> pd.DataFrame:
    """
    Parse the storage data from the ERCOT API. The data is returned in 5 minute intervals.
    """
    storage_data_json = get_data(url=RT_STORAGE_URL, session=session)
    df = pd.concat(
        [
            pd.DataFrame(storage_data_json["previousDay"]["data"]),
            pd.DataFrame(storage_data_json["currentDay"]["data"]),
        ]
    )
    df["datetime"] = pd.to_datetime(df["timestamp"]).dt.floor("5min")
    df.rename(columns={"netOutput": "battery_storage"}, inplace=True)
    df["battery_storage"] = -df["battery_storage"].astype(
        float
    )  # Storage is positive when charging'
    df = df[["battery_storage", "datetime"]].groupby("datetime").mean().reset_index()
    df.set_index("datetime", inplace=True)
    return df[["battery_storage"]]


def fetch_live_consumption(
    zone_key: str,
    session: Session | None = None,
    logger: Logger = getLogger(__name__),
) -> TotalConsumptionList:
    data_json = get_data(url=RT_CONSUMPTION_URL, session=session)
    consumption_list = TotalConsumptionList(logger)
    for key in ["previousDay", "currentDay"]:
        data_dict = data_json[key]
        dt = datetime.strptime(data_dict["dayDate"], "%Y-%m-%d %H:%M:%S%z").replace(
            tzinfo=TX_TZ
        )
        for item in data_dict["data"]:
            if "systemLoad" in item:
                consumption_list.append(
                    zoneKey=ZoneKey(zone_key),
                    datetime=dt.replace(hour=item["hourEnding"] - 1),
                    consumption=item["systemLoad"],
                    source=SOURCE,
                )
    return consumption_list


def fetch_live_production(
    zone_key: str,
    session: Session | None = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    """
    Fetch the live production data from the ERCOT API at a 5 minute interval.
    The data is returned in 5 minute intervals.
    """
    session = session or Session()
    gen_data_json = get_data(url=RT_GENERATION_URL, session=session)["data"]
    production_breakdowns = ProductionBreakdownList(logger)

    # Process storage data first - keep at 15-minute intervals
    df_storage = parse_storage_data_live(session)

    # Process generation data
    df_generation = process_generation_dataframe(
        pd.concat([pd.DataFrame(gen_data_json[day]).T for day in gen_data_json])
    )
    if not df_storage.empty:
        df_generation_storage = df_generation.merge(
            df_storage, left_index=True, right_index=True, how="inner"
        )
    else:
        df_generation_storage = df_generation.copy()

    # Round up to 2 decimals
    df_generation_storage = df_generation_storage.round(2)
    # Create production breakdowns for each timestamp - optimized version
    timestamps = df_generation_storage.index
    production_columns = [
        col for col in df_generation_storage.columns if col != "battery_storage"
    ]
    has_storage = "battery_storage" in df_generation_storage.columns

    # Use iloc for faster access instead of iterrows()
    for i, timestamp in enumerate(timestamps):
        production = ProductionMix()
        storage = StorageMix()

        # Get row data using iloc (faster than iterrows)
        row_data = df_generation_storage.iloc[i]

        # Add production values efficiently
        for col in production_columns:
            production.add_value(
                col,
                row_data[col],
                correct_negative_with_zero=True,
            )

        # Add storage data if available
        if has_storage:
            storage.add_value("battery", row_data["battery_storage"])

        # Add breakdown for each timestamp
        production_breakdowns.append(
            zoneKey=ZoneKey(zone_key),
            datetime=timestamp.to_pydatetime(),
            source=SOURCE,
            production=production,
            storage=storage,
        )

    return production_breakdowns


def _get_ercot_file(url: str, session: Session) -> bytes:
    """Downloads an ercot.com page or file through the proxy, which may leave it gzipped."""
    response = session.get(
        f"{US_PROXY}{urlparse(url).path}?{HOST_PARAMETER}", verify=False
    )
    response.raise_for_status()
    content = response.content
    return gzip.decompress(content) if content[:2] == b"\x1f\x8b" else content


# ponytail: the multi-year archive is ~50 MB and only changes once a year, so keep
# the last one in memory for the duration of a refetch. Yearly reports aren't cached,
# as ERCOT updates them in place every month.
@lru_cache(maxsize=1)
def _get_fuel_mix_archive(url: str) -> bytes:
    content = _get_ercot_file(url, Session())
    # Raising keeps a bad download out of the cache
    if not zipfile.is_zipfile(BytesIO(content)):
        raise ParserException(
            "US_ERCOT.py",
            f"{url} is not a zip ({len(content)} bytes starting with {content[:20]!r})",
        )
    return content


def _get_fuel_mix_workbook(year: int, session: Session) -> pd.ExcelFile:
    """Finds the Fuel Mix Report covering `year`: a workbook for recent years, a
    zip of workbooks for older ones."""
    page = _get_ercot_file(GENERATION_PAGE_URL, session).decode("utf-8", "replace")
    for href, text in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        title = re.search(
            r"Fuel Mix Report:\s*(\d{4})(?:\s*-\s*(\d{4}))?",
            re.sub("<[^>]+>", "", text),
        )
        if not title or not int(title[1]) <= year <= int(title[2] or title[1]):
            continue
        if not title[2]:
            return pd.ExcelFile(BytesIO(_get_ercot_file(href, session)))
        with zipfile.ZipFile(BytesIO(_get_fuel_mix_archive(href))) as archive:
            for name in archive.namelist():
                if name.lower().startswith(f"intgenbyfuel{year}."):
                    return pd.ExcelFile(BytesIO(archive.read(name)))
    raise ParserException(
        "US_ERCOT.py", f"No Fuel Mix Report found for {year} on {GENERATION_PAGE_URL}"
    )


def _interval_start(day: datetime, label: str) -> datetime:
    """Columns are local interval-ending times, "0:15" to "0:00". On the fall-back
    day, the repeated hour comes as extra "01:15 (DST)" to "02:00 (DST)" columns."""
    repeated_hour = label.endswith("(DST)")
    hours, minutes = map(int, label.removesuffix("(DST)").strip().split(":"))
    end_minutes = hours * 60 + minutes or 24 * 60
    start = datetime.combine(day.date(), datetime.min.time()) + timedelta(
        minutes=end_minutes - 15
    )
    return start.replace(tzinfo=TX_TZ, fold=int(repeated_hour)).astimezone(timezone.utc)


def parse_fuel_mix_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Turns a monthly sheet of the Fuel Mix Report (MWh per 15 minutes, one row
    per day and fuel) into MW per fuel, indexed by interval start in UTC."""
    df = df.rename(columns=lambda col: str(col).strip())
    fuel_column = "Fuel" if "Fuel" in df.columns else "Fuel Type"
    slots = [
        col
        for col in df.columns
        if col not in ("Date", fuel_column, "Settlement Type", "Total")
    ]
    values = df.dropna(subset=["Date"]).melt(
        id_vars=["Date", fuel_column], value_vars=slots, var_name="slot"
    )
    # Slots that don't exist (spring-forward hour, regular days' DST columns) are empty
    values = values.dropna(subset=["value"])
    values["datetime"] = [
        _interval_start(pd.Timestamp(day), slot)
        for day, slot in zip(values["Date"], values["slot"], strict=True)
    ]
    values["value"] = values["value"].astype(float) * 4  # MWh per 15 min to MW
    return values.pivot_table(
        index="datetime", columns=fuel_column, values="value", aggfunc="sum"
    )


def fetch_historical_production(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    """Reads the 28 days up to `target_datetime` from the Fuel Mix Report, which
    ERCOT publishes monthly, a few weeks after the end of each month."""
    start = target_datetime - timedelta(days=28)
    months = pd.period_range(
        start.astimezone(TX_TZ).replace(tzinfo=None),
        target_datetime.astimezone(TX_TZ).replace(tzinfo=None),
        freq="M",
    )
    workbooks = {}
    sheets = []
    for month in months:
        if month.year not in workbooks:
            workbooks[month.year] = _get_fuel_mix_workbook(month.year, session)
        sheets.append(
            parse_fuel_mix_sheet(workbooks[month.year].parse(month.strftime("%b")))
        )
    df = pd.concat(sheets)
    df = df[(df.index >= start) & (df.index <= target_datetime)]

    if df.empty or df.index.max() < target_datetime - timedelta(days=1):
        published = "no data" if df.empty else f"data only until {df.index.max()}"
        raise ParserException(
            "US_ERCOT.py",
            f"The Fuel Mix Report has {published} for {start} to {target_datetime}: "
            "ERCOT publishes each month a few weeks after it ends",
            zone_key,
        )
    unknown_fuels = set(df.columns) - FUEL_MIX_REPORT_FUELS
    if unknown_fuels:
        # A new category (e.g. for storage) could change what "Other" contains
        raise ParserException(
            "US_ERCOT.py",
            f"Unknown fuels in the Fuel Mix Report: {sorted(unknown_fuels)}",
            zone_key,
        )

    production_breakdowns = ProductionBreakdownList(logger)
    for dt, row in df.iterrows():
        dt = dt.to_pydatetime()
        row = row.dropna()
        production = ProductionMix()
        storage = StorageMix()
        battery_in_other = dt >= BATTERY_IN_OTHER_SINCE
        if battery_in_other:
            # Storage is positive when charging
            storage.add_value("battery", -(row.get("Other", 0) + row.get("WSL", 0)))
        for fuel, value in row.items():
            if fuel == "WSL" or (fuel == "Other" and battery_in_other):
                continue
            production.add_value(
                GENERATION_MAPPING[fuel], value, correct_negative_with_zero=True
            )
        production_breakdowns.append(
            zoneKey=ZoneKey(zone_key),
            datetime=dt,
            source=SOURCE,
            production=production,
            storage=storage,
        )
    return production_breakdowns


def fetch_live_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    data_json = get_data(url=RT_EXCHANGE_URL, session=session)
    all_data_points = []
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    for item in data_json["data"]:
        data_point = {}
        data_point["datetime"] = datetime.fromtimestamp(
            item["interval"] / 1000
        ).replace(second=0, tzinfo=TX_TZ)
        data_point["netFlow"] = sum(item[key] for key in EXCHANGE_MAPPING[zone_key2])

        all_data_points.append(data_point)

    # aggregate data points in the same minute interval
    aggregated_data_points = []
    for dt in sorted({item["datetime"] for item in all_data_points}):
        agg_data_point = {}
        agg_data_point["datetime"] = dt
        values_dt = [
            item["netFlow"] for item in all_data_points if item["datetime"] == dt
        ]
        agg_data_point["netFlow"] = sum(values_dt) / len(values_dt)
        agg_data_point["sortedZoneKeys"] = sortedZoneKeys
        agg_data_point["source"] = SOURCE
        aggregated_data_points.append(agg_data_point)
    validated_data_points = [x for x in all_data_points if validate_exchange(x, logger)]
    return validated_data_points


@refetch_frequency(timedelta(days=28))  # A month
def fetch_production(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
    if target_datetime is not None and target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)

    # The live feed only covers today and yesterday
    if target_datetime is None or target_datetime > datetime.now(
        timezone.utc
    ) - timedelta(days=1):
        production = fetch_live_production(
            zone_key=zone_key, session=session, logger=logger
        )
    else:
        production = fetch_historical_production(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
    return production.to_list()


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None or target_datetime >= datetime.now(tz=TX_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=1):
        consumption = fetch_live_consumption(
            zone_key=zone_key, session=session, logger=logger
        ).to_list()
    else:
        consumption = EIA.fetch_consumption(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
    return consumption


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    now = datetime.now(tz=TX_TZ)
    if target_datetime is None or target_datetime >= datetime.now(tz=TX_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    ):
        target_datetime = now
        exchanges = fetch_live_exchange(zone_key1, zone_key2, session, logger)

    else:
        exchanges = EIA.fetch_exchange(
            zone_key1, zone_key2, session, target_datetime, logger
        )
    return exchanges


def _get_publish_date(doc):
    return datetime.fromisoformat(doc["Document"]["PublishDate"])


def _find_document_by_publish_date(documents, target_date):
    """
    Find the latest document published on a specific date (ignoring time) or the latest document if no date is provided.

    Args:
        documents: List of document dictionaries
        target_date: A datetime object representing the date to search for (ignores time), or None to find the latest document

    Returns:
        The best matching document (or None if no match is found)
    """
    if target_date is None:
        # If no target_date is provided, return the latest document
        matching_docs = [
            doc for doc in documents if doc["Document"]["FriendlyName"][-3:] == "csv"
        ]
        return max(matching_docs, key=_get_publish_date, default=None)

    # If target_date is provided, find documents matching the specific date
    matching_docs = [
        doc
        for doc in documents
        if doc["Document"]["FriendlyName"][-3:] == "csv"
        and datetime.fromisoformat(doc["Document"]["PublishDate"]).date()
        == target_date.date()
    ]

    return max(matching_docs, key=_get_publish_date, default=None)


def _get_dataframe_from_url(url, session, target_date):
    response = session.get(url)
    docs = response.json()["ListDocsByRptTypeRes"]["DocumentList"]

    doc = _find_document_by_publish_date(docs, target_date)
    doc_id = doc["Document"]["DocID"]

    doc_url = f"{US_PROXY}/misdownload/servlets/mirDownload?doclookupId={doc_id}&{HOST_PARAMETER}"
    resp: Response = session.get(doc_url)  # verify=False

    # Open the ZIP file
    with zipfile.ZipFile(BytesIO(resp.content)) as z:
        # Extract the first file in the ZIP (assuming it contains a CSV)
        csv_filename = z.namelist()[0]
        with z.open(csv_filename) as f:
            df = pd.read_csv(f)

    return df


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests load forecast data in MW. target_datetime only date (takes the latest report on that date).
    If target_datetime is None, it takes the latest report created"""
    session = session or Session()

    url = f"{US_PROXY}/misapp/servlets/IceDocListJsonWS?reportTypeId={ReportTypeID.LOAD_FORECAST_REPORTID.value}&_{int(time.time())}&{HOST_PARAMETER}"
    df = _get_dataframe_from_url(url, session, target_datetime)

    # Transfrom Hour column
    df["HourStarting"] = df["HourEnding"].str.split(":", expand=True)[0].astype(int) - 1
    df["HourStarting"] = df["HourStarting"].astype(str) + ":00"

    all_consumption_events = (
        df.copy()
    )  # all events with a datetime and a consumption value
    consumption_list = TotalConsumptionList(logger)
    for _, row in all_consumption_events.iterrows():
        date_, time_ = row.DeliveryDate, row.HourStarting
        datetime_object = datetime.strptime(
            date_ + "T" + time_, "%m/%d/%YT%H:%M"
        ).replace(tzinfo=TX_TZ)
        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime_object,
            consumption=row.SystemTotal,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests wind and solar power data in MW. target_datetime only date (takes the latest report on that date).
    If target_datetime is None, it takes the latest report created"""
    session = session or Session()

    # Request wind power data
    url_wind = f"{US_PROXY}/misapp/servlets/IceDocListJsonWS?reportTypeId={ReportTypeID.WIND_POWER_PRODUCTION_REPORTID.value}&_{int(time.time())}&{HOST_PARAMETER}"
    df_wind = _get_dataframe_from_url(url_wind, session, target_datetime)

    # Request solar power data
    url_solar = f"{US_PROXY}/misapp/servlets/IceDocListJsonWS?reportTypeId={ReportTypeID.SOLAR_POWER_PRODUCTION_REPORTID.value}&_{int(time.time())}&{HOST_PARAMETER}"
    df_solar = _get_dataframe_from_url(url_solar, session, target_datetime)

    # Transfrom Hour column
    df_wind["HOUR_STARTING"] = df_wind["HOUR_ENDING"] - 1
    df_wind["HOUR_STARTING"] = df_wind["HOUR_STARTING"].astype(str) + ":00"
    df_solar["HOUR_STARTING"] = df_solar["HOUR_ENDING"] - 1
    df_solar["HOUR_STARTING"] = df_solar["HOUR_STARTING"].astype(str) + ":00"

    # Merge wind and solar into one dataframe
    merged_df = pd.merge(
        df_wind, df_solar, on=["DELIVERY_DATE", "HOUR_STARTING"], how="outer"
    )

    all_production_events = (
        merged_df.copy()
    )  # all events with a datetime and a production breakdown
    production_list = ProductionBreakdownList(logger)
    for _, event in all_production_events.iterrows():
        date_, time_ = event.DELIVERY_DATE, event.HOUR_STARTING
        datetime_object = datetime.strptime(
            date_ + "T" + time_, "%m/%d/%YT%H:%M"
        ).replace(tzinfo=TX_TZ)

        production_mix = ProductionMix()
        production_mix.add_value(
            "solar", event["STPPF_SYSTEM_WIDE"], correct_negative_with_zero=True
        )
        production_mix.add_value(
            "wind", event["STWPF_SYSTEM_WIDE"], correct_negative_with_zero=True
        )

        production_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=datetime_object,
            production=production_mix,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return production_list.to_list()


def fetch_dayahead_locational_marginal_price(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None:
        target_datetime = datetime.now(tz=TX_TZ)

    ERCOT_API_SUBSCRIPTION_KEY = get_token("ERCOT_API_SUBSCRIPTION_KEY")

    if not ERCOT_API_SUBSCRIPTION_KEY:
        raise ValueError("ERCOT_API_SUBSCRIPTION_KEY must be set")

    id_token = get_id_token()

    params = {
        "host": "https://api.ercot.com",
        "deliveryDateFrom": target_datetime.strftime("%Y-%m-%d"),
        "deliveryDateTo": target_datetime.strftime("%Y-%m-%d"),
    }
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Ocp-Apim-Subscription-Key": ERCOT_API_SUBSCRIPTION_KEY,
    }
    response = get_data(DAYAHEAD_LMP_URL, headers=headers, params=params)

    params["size"] = response["_meta"]["totalRecords"]

    response = get_data(DAYAHEAD_LMP_URL, headers=headers, params=params)

    prices = LocationalMarginalPriceList(logger)
    for row in response["data"]:
        if row[1] == "24:00":
            date = datetime.strptime(f"{row[0]} 00:00", "%Y-%m-%d %H:%M").replace(
                tzinfo=TX_TZ
            ) + timedelta(days=1)
        else:
            date = datetime.strptime(f"{row[0]} {row[1]}", "%Y-%m-%d %H:%M").replace(
                tzinfo=TX_TZ
            )
        prices.append(
            zoneKey=zone_key,
            datetime=date,
            price=row[3],
            currency="USD",
            node=row[2],
            source=SOURCE,
        )
    return prices.to_list()


def fetch_realtime_locational_marginal_price(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None:
        target_datetime = datetime.now(tz=TX_TZ)

    ERCOT_API_SUBSCRIPTION_KEY = get_token("ERCOT_API_SUBSCRIPTION_KEY")

    if not ERCOT_API_SUBSCRIPTION_KEY:
        raise ValueError("ERCOT_API_SUBSCRIPTION_KEY must be set")

    id_token = get_id_token()

    start_datetime = target_datetime - timedelta(minutes=40)
    end_datetime = target_datetime + timedelta(minutes=10)

    params = {
        "host": "https://api.ercot.com",
        "SCEDTimestampTo": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
        "SCEDTimestampFrom": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Ocp-Apim-Subscription-Key": ERCOT_API_SUBSCRIPTION_KEY,
    }
    response = get_data(REALTIME_LMP_URL, headers=headers, params=params)

    params["size"] = response["_meta"]["totalRecords"]

    response = get_data(REALTIME_LMP_URL, headers=headers, params=params)

    prices = LocationalMarginalPriceList(logger)
    for row in response["data"]:
        date = datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=TX_TZ)
        prices.append(
            zoneKey=zone_key,
            datetime=date,
            price=row[3],
            currency="USD",
            node=row[2],
            source=SOURCE,
        )
    return prices.to_list()


def process_generation_dataframe(df):
    """
    Process generation DataFrame by:
    1. Flooring timestamps to nearest 5 minutes
    2. Extracting 'gen' values from dictionary format
    3. Grouping by datetime index and taking mean (temporal aggregation)
    4. Standardizing columns using GENERATION_MAPPING (column aggregation)
    """
    df_processed = df.copy()

    # Convert to DatetimeIndex if it isn't already
    if not isinstance(df_processed.index, pd.DatetimeIndex):
        df_processed.index = pd.to_datetime(df_processed.index)

    df_processed.index = df_processed.index.floor("5min")

    # Unmapped keys (e.g. the "Power Storage" split, see GENERATION_MAPPING) would crash ProductionMix
    df_processed = df_processed[
        [col for col in df_processed.columns if col in GENERATION_MAPPING]
    ]

    # Extract 'gen' values from dictionaries
    df_processed = df_processed.apply(
        lambda col: col.apply(
            lambda x: x["gen"] if isinstance(x, dict) and "gen" in x else None
        )
    )

    # First group by datetime index to aggregate multiple rows with same 5-minute timestamp
    df_processed = df_processed.groupby(df_processed.index).mean()

    # Then group columns by their target names and sum (for columns that map to same target)
    column_mapping = pd.Series(
        {col: GENERATION_MAPPING[col] for col in df_processed.columns}
    )
    df_generation_standardized = df_processed.groupby(column_mapping, axis=1).sum(
        numeric_only=True,
    )

    return df_generation_standardized[
        [col for col in df_generation_standardized.columns if col != "battery"]
    ]


def get_id_token():
    ERCOT_API_PASSWORD = get_token("ERCOT_API_PASSWORD")
    ERCOT_API_USERNAME = get_token("ERCOT_API_USERNAME")

    if not ERCOT_API_PASSWORD or not ERCOT_API_USERNAME:
        raise ValueError("ERCOT_API_PASSWORD and ERCOT_API_USERNAME must be set")

    auth_url = f"{AUTH_URL_ERCOT}?username={ERCOT_API_USERNAME}&password={ERCOT_API_PASSWORD}&grant_type=password&scope=openid+fec253ea-0d06-4272-a5e6-b478baeecd70+offline_access&client_id=fec253ea-0d06-4272-a5e6-b478baeecd70&response_type=id_token"

    auth_response = requests.post(auth_url)
    return auth_response.json().get("id_token")


if __name__ == "__main__":
    "Main method, not used by Electricity Map backend, but handy for testing"

    from pprint import pprint

    pprint(fetch_production())
    # pprint(fetch_production(target_datetime = datetime(2023,5,14)))

    # pprint(parse_storage_data(session=Session()))
    # print("fetch_consumption_forecast() -->")
    # pprint(fetch_consumption_forecast(target_datetime=datetime(2025,3,14)))
    # pprint(fetch_consumption_forecast())

    # print("fetch_wind_solar_forecasts() -->")
    # pprint(fetch_wind_solar_forecasts())
