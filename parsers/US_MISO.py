#!/usr/bin/env python3

"""Parser for the MISO area of the United States."""

from datetime import datetime
from logging import Logger, getLogger
from typing import Any

from dateutil import parser, tz
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import EventSourceType, ProductionMix

SOURCE = "misoenergy.org"
ZONE = "US-MIDW-MISO"
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
# "The category listed as “Other” is the combination of Hydro, Pumped Storage Hydro, Diesel, Demand Response Resources,
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

    """
    for item in raw_data_wind:
        dt = parser.parse(item["DateTimeEST"]).replace(
            tzinfo=tz.gettz("America/New_York")
        )
        mix = ProductionMix(wind=float(item["Value"]))

        production_breakdowns.append(
            datetime=dt,
            production=mix,
            source=SOURCE,
            zoneKey=zone_key,
            sourceType=EventSourceType.forecasted,
        )
    """

    for wind_event, solar_event in zip(raw_data_wind, raw_data_solar, strict=True):
        # Check that we loop over same dates
        if wind_event["DateTimeEST"] == solar_event["DateTimeEST"]:
            dt = parser.parse(wind_event["DateTimeEST"]).replace(
                tzinfo=tz.gettz("America/New_York")
            )

            mix = ProductionMix(
                wind=float(wind_event["Value"]), solar=float(solar_event["Value"])
            )

            production_breakdowns.append(
                datetime=dt,
                production=mix,
                source=SOURCE,
                zoneKey=zone_key,
                sourceType=EventSourceType.forecasted,
            )

    return production_breakdowns.to_list()


if __name__ == "__main__":
    # print("fetch_production() ->")
    # print(fetch_production())
    print("fetch_wind_solar_forecasts() ->")
    print(fetch_wind_solar_forecasts())
