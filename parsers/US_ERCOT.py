"""Parser for the ERCOT grid area of the United States."""

import gzip
import json
import zipfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Response, Session

import parsers.EIA as EIA
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.validation import validate_exchange

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

# These links are found at https://www.ercot.com/gridinfo/generation, and should be updated as new data is released
HISTORICAL_GENERATION_URL = {
    "2024": f"{US_PROXY}/files/docs/2024/02/08/IntGenbyFuel2024.xlsx?{HOST_PARAMETER}",
    "2023": f"{US_PROXY}/files/docs/2023/02/07/IntGenbyFuel2023.xlsx?{HOST_PARAMETER}",
    "2022": f"{US_PROXY}/files/docs/2022/02/08/IntGenbyFuel2022.xlsx?{HOST_PARAMETER}",
    "2021": f"{US_PROXY}/files/docs/2021/02/08/IntGenbyFuel2021.xlsx?{HOST_PARAMETER}",
    "all_previous": f"{US_PROXY}/files/docs/2021/03/10/FuelMixReport_PreviousYears.zip?{HOST_PARAMETER}",
}

GENERATION_MAPPING = {
    "Coal and Lignite": "coal",
    "Hydro": "hydro",
    "Natural Gas": "gas",
    "Nuclear": "nuclear",
    "Other": "unknown",
    "Power Storage": "battery",
    "Solar": "solar",
    "Wind": "wind",
    "WSL": "battery",
    "Biomass": "biomass",
    "Gas": "gas",
    "Coal": "coal",
    "Gas-CC": "gas",
}
EXCHANGE_MAPPING = {"US-CENT-SWPP": ["dcE", "dcN"], "MX-NE": ["dcL"], "MX-NO": ["dcR"]}


def get_data(url: str, session: Session | None = None):
    """requests ERCOT url and return json"""
    if not session:
        session = Session()

    resp: Response = session.get(url, verify=False)
    response_text = gzip.decompress(resp.content).decode("utf-8")
    data_json = json.loads(response_text)
    return data_json


def parse_storage_data(session: Session):
    storage_data_json = get_data(url=RT_STORAGE_URL, session=session)

    storage_by_hour = {}
    for day_key in ["previousDay", "currentDay"]:
        if day_key not in storage_data_json:
            continue

        for entry in storage_data_json[day_key]["data"]:
            dt = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S%z").replace(
                tzinfo=TX_TZ
            )
            hour_dt = dt.replace(minute=0, second=0, microsecond=0)

            if hour_dt not in storage_by_hour:
                storage_by_hour[hour_dt] = []

            storage_by_hour[hour_dt].append(entry["netOutput"])

    return storage_by_hour


def fetch_live_consumption(
    zone_key: str,
    session: Session | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    data_json = get_data(url=RT_CONSUMPTION_URL, session=session)
    all_data_points = []
    for key in ["previousDay", "currentDay"]:
        data_dict = data_json[key]
        dt = datetime.strptime(data_dict["dayDate"], "%Y-%m-%d %H:%M:%S%z").replace(
            tzinfo=TX_TZ
        )
        for item in data_dict["data"]:
            if "systemLoad" in item:
                data_point = {
                    "datetime": dt.replace(hour=item["hourEnding"] - 1),
                    "consumption": item["systemLoad"],
                    "zoneKey": zone_key,
                    "source": SOURCE,
                }
                all_data_points.append(data_point)
    return all_data_points


def fetch_live_production(
    zone_key: str,
    session: Session | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    gen_data_json = get_data(url=RT_GENERATION_URL, session=session)["data"]
    all_data_points = []

    # Process storage data first
    storage_by_hour = parse_storage_data(session)

    # Process generation data
    for day in gen_data_json:
        date_dict = gen_data_json[day]
        hourly_data = {}

        for date in date_dict:
            dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S%z").replace(tzinfo=TX_TZ)
            hour_dt = dt.replace(minute=0, second=0, microsecond=0)

            if hour_dt not in hourly_data:
                hourly_data[hour_dt] = {
                    mode: [] for mode in GENERATION_MAPPING.values()
                }

            for mode, data in date_dict[date].items():
                production_source = GENERATION_MAPPING[mode]
                if production_source != "battery":  # Skip battery from generation data
                    hourly_data[hour_dt][production_source].append(data["gen"])

        for hour_dt, modes in hourly_data.items():
            production = {}
            storage = {}

            # Add generation data
            for mode, values in modes.items():
                if values:
                    production[mode] = sum(values) / len(values)

            # Add storage data if available for this hour
            if hour_dt in storage_by_hour:
                storage_values = storage_by_hour[hour_dt]
                if storage_values:
                    storage["battery"] = sum(storage_values) / len(storage_values)

            all_data_points.append(
                {
                    "zoneKey": zone_key,
                    "datetime": hour_dt,
                    "production": production,
                    "storage": storage,
                    "source": SOURCE,
                }
            )

    return all_data_points


def get_sheet_from_date(year: int, month: str, session: Session | None = None):
    if not session:
        session = Session()

    if year > 2020:
        url = HISTORICAL_GENERATION_URL[str(year)]
        return pd.read_excel(url, engine="openpyxl", sheet_name=month)
    else:
        url = HISTORICAL_GENERATION_URL["all_previous"]
        response = session.get(url)

        if response.content.startswith(b"PK"):
            zip_data = BytesIO(response.content)
        else:
            try:
                decompressed = gzip.decompress(response.content)
                zip_data = BytesIO(decompressed)
            except gzip.BadGzipFile as err:
                raise ValueError("File is neither a ZIP nor a gzipped file") from err

        year_file = f"IntGenbyFuel{year}.xlsx"

        with zipfile.ZipFile(zip_data) as zf:
            if year_file not in zf.namelist():
                raise NotImplementedError(
                    f"Data for year {year} not found in historical data"
                )
            with zf.open(year_file) as excel_file:
                return pd.read_excel(excel_file, engine="openpyxl", sheet_name=month)


def fetch_historical_production(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)

    end = target_datetime + timedelta(hours=1)
    start = end - timedelta(days=1)
    year = target_datetime.year
    month = target_datetime.strftime("%b")

    all_data_points = []

    df = get_sheet_from_date(year, month, session)

    df["Date"] = pd.to_datetime(df["Date"])
    time_columns = df.columns[4:]
    datapoints_by_date = {}

    for _, row in df.iterrows():
        date = datetime.strptime(str(row["Date"]), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=TX_TZ
        )
        if date < (start + timedelta(days=-1)) or date > (end + timedelta(days=1)):
            continue

        production_source = GENERATION_MAPPING[row["Fuel"]]

        for hour in range(0, 24):
            hour_dt = date + timedelta(hours=hour)

            if hour_dt < start or hour_dt > end:
                continue

            # We get the data in 15 minute intervals, so we need to sum the 4 columns that represent an hour
            start_idx = hour * 4
            end_idx = start_idx + 4
            hour_cols = time_columns[start_idx:end_idx]
            hour_value = row[hour_cols].sum()

            if hour_dt not in datapoints_by_date:
                datapoints_by_date[hour_dt] = {"storage": {}, "production": {}}

            target = "storage" if production_source == "battery" else "production"
            datapoints_by_date[hour_dt][target].update({production_source: hour_value})

    for hour_dt, production_and_storage in datapoints_by_date.items():
        production = production_and_storage.get("production", {})
        storage = production_and_storage.get("storage", {})
        data_point = {
            "zoneKey": zone_key,
            "datetime": hour_dt,
            "production": production,
            "storage": storage,
            "source": SOURCE,
        }
        all_data_points.append(data_point)

    return all_data_points


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


def fetch_production(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None or target_datetime > (
        datetime.now(tz=timezone.utc) - timedelta(days=1)
    ).replace(tzinfo=target_datetime.tzinfo if target_datetime else timezone.utc):
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
    return production


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
        )
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
