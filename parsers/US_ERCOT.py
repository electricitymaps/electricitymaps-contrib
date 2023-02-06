"""Parser for the ERCOT grid area of the United States."""


import gzip
import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
import pytz
from requests import Response, Session

import parsers.EIA as EIA
from parsers.lib.validation import validate_exchange

TX_TZ = pytz.timezone("US/Central")
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

GENERATION_MAPPING = {
    "Coal and Lignite": "coal",
    "Hydro": "hydro",
    "Natural Gas": "gas",
    "Nuclear": "nuclear",
    "Other": "unknown",
    "Power Storage": "unknown",  # we lose this information in the EIA parser and have no easy way to split it when we run fetch_production for past dates. As it is a minor share of the production mix, it will be categorized as unknown
    "Solar": "solar",
    "Wind": "wind",
}
EXCHANGE_MAPPING = {"US-CENT-SWPP": ["dcE", "dcN"], "MX-NE": ["dcL"], "MX-NO": ["dcR"]}


def get_data(url: str, session: Session):
    """requests ERCOT url and return json"""
    r: Response = session.get(url)
    response_text = gzip.decompress(r.content).decode("utf-8")
    data_json = json.loads(response_text)
    return data_json


def fetch_live_consumption(
    zone_key: str,
    session: Session,
    logger: Logger = getLogger(__name__),
) -> list:
    data_json = get_data(url=RT_CONSUMPTION_URL, session=session)
    all_data_points = []
    for key in ["previousDay", "currentDay"]:
        data_dict = data_json[key]
        dt = arrow.get(data_dict["dayDate"]).datetime.replace(tzinfo=TX_TZ)
        for item in data_dict["data"]:
            if "systemLoad" in item:
                data_point = {
                    "datetime": dt.replace(hour=item["hourEnding"] - 1),
                    "consumption": item["systemLoad"],
                    "zoneKey": zone_key,
                    "source": "ercot.com",
                }
                all_data_points.append(data_point)
    return all_data_points


def fetch_live_production(
    zone_key: str,
    session: Session,
    logger: Logger = getLogger(__name__),
) -> list:
    data_json = get_data(url=RT_GENERATION_URL, session=session)["data"]
    data_dict = {}
    for key in data_json:
        data_dict = {**data_dict, **data_json[key]}
    all_data_points = []
    for date_key in data_json:
        date_dict = data_json[date_key]
        for date_key in data_json:
            date_dict = data_json[date_key]
            for item in date_dict:
                production = {}
                dt = arrow.get(item).datetime.replace(tzinfo=TX_TZ)
                for mode in date_dict[item]:
                    value = date_dict[item][mode]["gen"]
                    production[GENERATION_MAPPING[mode]] = value
                data_point = {
                    "zoneKey": zone_key,
                    "datetime": dt,
                    "production": production,
                    "source": "ercot.com",
                }
                all_data_points.append(data_point)
    return all_data_points


def fetch_live_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
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
    for dt in sorted(list(set([item["datetime"] for item in all_data_points]))):
        agg_data_point = {}
        agg_data_point["datetime"] = dt
        values_dt = [
            item["netFlow"] for item in all_data_points if item["datetime"] == dt
        ]
        agg_data_point["netFlow"] = sum(values_dt) / len(values_dt)
        agg_data_point["sortedZoneKeys"] = sortedZoneKeys
        agg_data_point["source"] = "ercot.com"
        aggregated_data_points.append(agg_data_point)
    validated_data_points = [x for x in all_data_points if validate_exchange(x, logger)]
    return validated_data_points


def fetch_production(
    zone_key: str = "US-TEX-ERCO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    now = datetime.now(tz=pytz.utc)
    if (
        target_datetime is None
        or target_datetime > arrow.get(now).floor("day").shift(days=-1).datetime
    ):
        production = fetch_live_production(
            zone_key=zone_key, session=session, logger=logger
        )
    else:
        production = EIA.fetch_production_mix(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
    return production


def fetch_consumption(
    zone_key: str = "US-TEX-ERCO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    now = datetime.now(tz=pytz.UTC)
    if (
        target_datetime is None
        or target_datetime > arrow.get(now).floor("day").shift(days=-1).datetime
    ):
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
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    now = datetime.now(tz=TX_TZ)
    if (
        target_datetime is None
        or target_datetime > arrow.get(now).floor("day").datetime
    ):
        target_datetime = now
        exchanges = fetch_live_exchange(zone_key1, zone_key2, session, target_datetime)

    else:
        exchanges = EIA.fetch_exchange(zone_key1, zone_key2, session, target_datetime)
    return exchanges
