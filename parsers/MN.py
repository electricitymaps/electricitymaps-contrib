#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.exceptions import ParserException

NDC_GENERATION = "https://disnews.energy.mn/convertt.php"
TZ = ZoneInfo("Asia/Ulaanbaatar")  # UTC+8

# Query fields to web API fields
JSON_QUERY_TO_SRC = {
    "time": "date",
    "consumptionMW": "syssum",
    "solarMW": "sumnar",
    "windMW": "sums",
    "importMW": "energyimport",  # positive = import
    "temperatureC": "t",  # current temperature
}


def parse_json(web_json: dict, logger: Logger, zone_key: ZoneKey) -> dict[str, Any]:
    """
    Parse the fetched JSON data to our query format according to JSON_QUERY_TO_SRC.
    Example of expected JSON format present at URL:
    {"date":"2023-06-27 18:00:00","syssum":"869.37","sumnar":42.34,"sums":119.79,"energyimport":"49.58"}
    """

    # Validate first if keys in fetched dict match expected keys
    if set(JSON_QUERY_TO_SRC.values()) != set(web_json.keys()):
        logger.error(
            msg=f"Fetched keys from source {web_json.keys()} do not match expected keys {JSON_QUERY_TO_SRC.values()}.",
            extra={"zone_key": zone_key, "parser": "MN.py"},
        )

    if None in web_json.values():
        raise ParserException(
            parser="MN.py",
            message=f"Fetched values contain null. Fetched data: {web_json}.",
        )

    # Then we can safely parse them
    query_data = {}
    for query_key, src_key in JSON_QUERY_TO_SRC.items():
        if "time" in query_key:
            # convert to datetime
            query_data[query_key] = datetime.fromisoformat(web_json[src_key]).replace(
                tzinfo=TZ
            )
        else:
            # or convert to float, might also be string
            query_data[query_key] = float(web_json[src_key])

    return query_data


def query(session: Session, logger: Logger, zone_key: ZoneKey) -> dict[str, Any]:
    """
    Query the JSON endpoint and parse it.
    """

    target_response: Response = session.get(NDC_GENERATION)

    if not target_response.ok:
        raise ParserException(
            parser="MN.py",
            message=f"Data request did not succeed: {target_response.status_code}",
        )

    # Read as JSON
    response_json = target_response.json()
    query_result = parse_json(response_json, logger, zone_key)

    return query_result


def fetch_production(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")

    query_data = query(session, logger, zone_key)

    # Calculated 'unknown' production from available data (consumption, import, solar, wind, tpp).
    # 'unknown' consists of 92.8% coal, 5.8% oil and 1.4% hydro as per 2020; sources: IEA and IRENA statistics.
    query_data["leftoverMW"] = round(
        query_data["consumptionMW"]
        - query_data["importMW"]
        - query_data["solarMW"]
        - query_data["windMW"],
        13,
    )

    prod_mix = ProductionMix()
    prod_mix.add_value("solar", query_data["solarMW"])
    prod_mix.add_value("wind", query_data["windMW"])
    prod_mix.add_value("unknown", query_data["leftoverMW"])

    prod_breakdown_list = ProductionBreakdownList(logger)
    prod_breakdown_list.append(
        datetime=query_data["time"],
        zoneKey=zone_key,
        source="https://ndc.energy.mn/",
        production=prod_mix,
    )

    return prod_breakdown_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")

    query_data = query(session, logger, zone_key)

    consumption_list = TotalConsumptionList(logger)
    consumption_list.append(
        datetime=query_data["time"],
        zoneKey=zone_key,
        consumption=query_data["consumptionMW"],
        source="https://ndc.energy.mn/",
    )

    return consumption_list.to_list()


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production(ZoneKey("MN")))
    print("fetch_consumption() ->")
    print(fetch_consumption(ZoneKey("MN")))
