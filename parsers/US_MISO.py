#!/usr/bin/env python3

"""Parser for the MISO area of the United States."""

import io
from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
from dateutil import parser, tz
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    GridAlertList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    GridAlertType,
    ProductionMix,
)

SOURCE = "misoenergy.org"
ZONE = "US-MIDW-MISO"
TIMEZONE = ZoneInfo("America/New_York")

mix_url = (
    "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType"
    "=getfuelmix&returnType=json"
)

mapping = {
    "Coal": "coal",
    "Natural Gas": "gas",
    "Nuclear": "nuclear",
    "Wind": "wind",
    "Solar": "solar",
    "Other": "unknown",
}

wind_forecast_url = "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getWindForecast&returnType=json"
solar_forecast_url = "https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getSolarForecast&returnType=json"

# To quote the MISO data source;
# "The category listed as "Other" is the combination of Hydro, Pumped Storage Hydro, Diesel, Demand Response Resources,
# External Asynchronous Resources and a varied assortment of solid waste, garbage and wood pulp burners".

# Timestamp reported by data source is in format 23-Jan-2018 - Interval 11:45 EST
# Unsure exactly why EST is used, possibly due to operational connections with PJM.


def get_json_data(logger: Logger, session: Session | None = None) -> dict:
    """Returns 5 minute generation data in json format."""

    s = session or Session()
    json_data = s.get(mix_url).json()

    return json_data


def data_processer(json_data, logger: Logger) -> tuple[datetime, ProductionMix]:
    """
    Identifies any unknown fuel types and logs a warning.
    Returns a tuple containing datetime object and production dictionary.
    """

    generation = json_data["Fuel"]["Type"]

    mix = ProductionMix()
    for fuel in generation:
        try:
            k = mapping[fuel["CATEGORY"]]
        except KeyError:
            logger.warning(
                "Key '{}' is missing from the MISO fuel mapping.".format(
                    fuel["CATEGORY"]
                )
            )
            k = "unknown"
        mix.add_value(k, float(fuel["ACT"]))

    # Remove unneeded parts of timestamp to allow datetime parsing.
    timestamp = json_data["RefId"]
    split_time = timestamp.split(" ")
    time_junk = {1, 2}  # set literal
    useful_time_parts = [v for i, v in enumerate(split_time) if i not in time_junk]

    if useful_time_parts[-1] != "EST":
        raise ValueError("Timezone reported for US-MISO has changed.")

    time_data = " ".join(useful_time_parts)
    tzinfos = {"EST": tz.gettz("America/New_York")}
    dt = parser.parse(time_data, tzinfos=tzinfos)

    return dt, mix


def fetch_production(
    zone_key: ZoneKey = ZoneKey(ZONE),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    json_data = get_json_data(logger, session=session)
    dt, mix = data_processer(json_data, logger)

    production_breakdowns = ProductionBreakdownList(logger)
    production_breakdowns.append(
        zoneKey=zone_key,
        datetime=dt,
        production=mix,
        source=SOURCE,
    )
    return production_breakdowns.to_list()


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZoneKey(ZONE),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the 6 days ahead load (in MW) hourly data."""
    session = session or Session()

    # Datetime
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    else:
        # assume passed in correct timezone
        target_datetime = target_datetime.replace(tzinfo=TIMEZONE)

    # Request data
    url = f"https://docs.misoenergy.org/marketreports/{target_datetime.strftime('%Y%m%d')}_df_al.xls"
    response = session.get(
        url, verify=False
    )  # use requests library with verification disabled
    df = pd.read_excel(
        io.BytesIO(response.content), sheet_name="Sheet1", skiprows=4, skipfooter=1
    )

    # Process dataframe
    df = df.dropna(subset=["HourEnding"])
    df = df.loc[df["HourEnding"] != "HourEnding"]
    df.loc[:, "HourEnding"] = df["HourEnding"].astype(int)
    df["Interval End"] = pd.to_datetime(df["Market Day"]) + pd.to_timedelta(
        df["HourEnding"], unit="h"
    )
    df["Interval Start"] = df["Interval End"] - pd.Timedelta(hours=1)

    # Record events in consumption_list
    all_consumption_events = df.copy()
    consumption_list = TotalConsumptionList(logger)
    for _, event in all_consumption_events.iterrows():
        event_datetime = event["Interval Start"].strftime("%Y-%m-%d %H:%M:%S")
        event_datetime = datetime.fromisoformat(event_datetime).replace(tzinfo=TIMEZONE)
        consumption_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            consumption=float(event["MISO MTLF (MWh)"]),
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = ZoneKey(ZONE),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the day ahead wind and solar forecast (in MW) hourly data."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    s = session or Session()

    # Request wind data
    req_wind = s.get(wind_forecast_url)
    raw_json_wind = req_wind.json()
    raw_data_wind = raw_json_wind["Forecast"]

    # Request solar data
    req_solar = s.get(solar_forecast_url)
    raw_json_solar = req_solar.json()
    raw_data_solar = raw_json_solar["Forecast"]

    production_breakdowns = ProductionBreakdownList(logger)

    for wind_event, solar_event in zip(raw_data_wind, raw_data_solar, strict=True):
        # Check that we loop over same dates
        if wind_event["DateTimeEST"] == solar_event["DateTimeEST"]:
            dt = parser.parse(wind_event["DateTimeEST"]).replace(tzinfo=TIMEZONE)

            production_mix = ProductionMix()
            production_mix.add_value(
                "wind", float(wind_event["Value"]), correct_negative_with_zero=True
            )
            production_mix.add_value(
                "solar", float(solar_event["Value"]), correct_negative_with_zero=True
            )

            production_breakdowns.append(
                datetime=dt,
                production=production_mix,
                source=SOURCE,
                zoneKey=zone_key,
                sourceType=EventSourceType.forecasted,
            )

    return production_breakdowns.to_list()


def fetch_grid_alerts(
    zone_key: ZoneKey = ZoneKey(ZONE),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetch Grid Alerts from MISO"""
    session = session or Session()

    # API URL
    url = "https://www.misoenergy.org/api/topicnotifications/getrecentnotifications"

    # Request payload (can be adjusted if you want specific filters)
    payload = {"topics": ["RealTime"], "take": 0}  # take 0 is equal to get all possible
    # TODO: do we just need the last one?

    # Request headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.misoenergy.org/markets-and-operations/notifications/real-time-operations-notifications/",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Make the POST request
    response = session.post(url, json=payload, headers=headers)

    # Check for success
    if response.status_code == 200:
        notifications = response.json()

    # TODO: maybe extract locationRegion from each notification?
    # TODO: maybe extract startTime and endTime from each notification?
    # TODO: maybe extract alertType from each notification?

    # Record events in grid_alert_list
    grid_alert_list = GridAlertList(logger)
    for notification in notifications:
        publish_datetime = datetime.fromisoformat(
            notification["publishDateUnformatted"]
        )  # in UTC

        clean_subject = extract_text_with_links(notification["subject"])
        clean_body = extract_text_with_links(notification["body"])
        message = clean_subject + "\n" + clean_body

        grid_alert_list.append(
            zoneKey=zone_key,
            locationRegion=None,
            source=SOURCE,
            alertType=GridAlertType.undefined,
            message=message,
            issuedTime=publish_datetime,
            startTime=None,  # if None, it defaults to issuedTime
            endTime=None,
        )
    return grid_alert_list.to_list()

def extract_text_with_links(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for a in soup.find_all('a'):
        if a.get('href'):
            a.replace_with(f"{a.get_text()} ({a['href']})")
    return soup.get_text()

if __name__ == "__main__":
    from pprint import pprint

    print("fetch_production() ->")
    print(fetch_production())

    print(fetch_consumption_forecast())

    print("fetch_wind_solar_forecasts() ->")
    print(fetch_wind_solar_forecasts())

    pprint(fetch_grid_alerts())
