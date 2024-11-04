"""Parser for the ERCOT grid area of the United States."""

import gzip
import json
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import arrow
from requests import Response, Session

import parsers.EIA as EIA
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.validation import validate_exchange

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
    resp: Response = session.get(url, verify=False)
    response_text = gzip.decompress(resp.content).decode("utf-8")
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
    all_data_points = []
    for date_key in data_json:
        date_dict = data_json[date_key]
        for date_key in data_json:
            print(f"date_key: {date_key}")
            date_dict = data_json[date_key]

            hourly_data = {}
            for item in date_dict:
                dt = datetime.strptime(item, "%Y-%m-%d %H:%M:%S%z").replace(
                    tzinfo=TX_TZ
                )
                hour_dt = dt.replace(minute=0, second=0, microsecond=0)

                if hour_dt not in hourly_data:
                    hourly_data[hour_dt] = {}
                    for mode in GENERATION_MAPPING.values():
                        hourly_data[hour_dt][mode] = []

                for mode in date_dict[item]:
                    mapped_mode = GENERATION_MAPPING[mode]
                    value = date_dict[item][mode]["gen"]
                    hourly_data[hour_dt][mapped_mode].append(value)

            for hour_dt, modes in hourly_data.items():
                production = {}
                for mode, values in modes.items():
                    if values:
                        production[mode] = sum(values) / len(values)
                    else:
                        production[mode] = 0

                data_point = {
                    "zoneKey": zone_key,
                    "datetime": hour_dt,
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
    for dt in sorted({item["datetime"] for item in all_data_points}):
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
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session = Session(),
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
        production = EIA.fetch_production_mix(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
    return production


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("US-TEX-ERCO"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    now = datetime.now(tz=timezone.utc)
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
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    now = datetime.now(tz=TX_TZ)
    if (
        target_datetime is None
        or target_datetime > arrow.get(now).floor("day").datetime
    ):
        target_datetime = now
        exchanges = fetch_live_exchange(zone_key1, zone_key2, session, logger)

    else:
        exchanges = EIA.fetch_exchange(
            zone_key1, zone_key2, session, target_datetime, logger
        )
    return exchanges
