"""Parser for the ERCOT grid area of the United States."""

import gzip
import json
import time
import zipfile
from datetime import datetime, timedelta, timezone
from enum import Enum
from io import BytesIO
from logging import Logger, getLogger
from typing import Any
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
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.utils import get_token
from electricitymap.contrib.parsers.lib.validation import validate_exchange

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
    session = session or Session()
    gen_data_json = get_data(url=RT_GENERATION_URL, session=session)["data"]
    production_breakdowns = ProductionBreakdownList(logger)

    # Process storage data first
    # storage_by_hour = parse_storage_data(session)

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
            production = ProductionMix()
            # storage = StorageMix()

            # Add generation data
            for mode, values in modes.items():
                if values:
                    production.add_value(
                        mode,
                        (sum(values) / len(values)),
                        correct_negative_with_zero=True,
                    )

            # Add storage data if available for this hour
            # if hour_dt in storage_by_hour:
            #     storage_values = storage_by_hour[hour_dt]
            #     if storage_values:
            #         storage.add_value(
            #             "battery", sum(storage_values) / len(storage_values)
            #         )

            production_breakdowns.append(
                zoneKey=ZoneKey(zone_key),
                datetime=hour_dt,
                source=SOURCE,
                production=production,
                # storage=storage,
            )

    return production_breakdowns


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
) -> ProductionBreakdownList:
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)

    year = target_datetime.year
    month = target_datetime.strftime("%b")

    production_breakdowns = ProductionBreakdownList(logger)

    df = get_sheet_from_date(year, month, session)

    df["Date"] = pd.to_datetime(df["Date"])
    time_columns = df.columns[4:]
    datapoints_by_date = {}

    for _, row in df.iterrows():
        date = datetime.strptime(str(row["Date"]), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=TX_TZ
        )

        production_source = GENERATION_MAPPING[row["Fuel"]]

        for hour in range(0, 24):
            hour_dt = date + timedelta(hours=hour)

            # We get the data in 15 minute intervals, so we need to sum the 4 columns that represent an hour
            start_idx = hour * 4
            end_idx = start_idx + 4
            hour_cols = time_columns[start_idx:end_idx]
            hour_value = row[hour_cols].sum()

            if hour_dt not in datapoints_by_date:
                datapoints_by_date[hour_dt] = {
                    "storage": StorageMix(),
                    "production": ProductionMix(),
                }

            target = "storage" if production_source == "battery" else "production"
            datapoints_by_date[hour_dt][target].add_value(production_source, hour_value)

    for hour_dt, production_and_storage in datapoints_by_date.items():
        production = production_and_storage.get("production", ProductionMix())
        # storage = production_and_storage.get("storage", StorageMix())

        production_breakdowns.append(
            zoneKey=ZoneKey(zone_key),
            datetime=hour_dt,
            source=SOURCE,
            production=production,
            # storage=storage,
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

    # print("fetch_consumption() ->")
    # pprint(fetch_consumption())

    # print("fetch_consumption_forecast() -->")
    # pprint(fetch_consumption_forecast(target_datetime=datetime(2025,3,14)))
    pprint(fetch_consumption_forecast())

    # print("fetch_wind_solar_forecasts() -->")
    # pprint(fetch_wind_solar_forecasts())
