#!/usr/bin/python3

import json
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

# RU-1: European and Uralian Market Zone (Price Zone 1)
# RU-2: Siberian Market Zone (Price Zone 2)
# RU-AS: Russia East Power System (2nd synchronous zone)
# Handling of hours: data at t on API side corresponds to
# production / consumption from t to t+1

# http://br.so-ups.ru is not available outside Russia (sometimes?), use a reverse proxy in Russia
HOST = "https://858127-cc16935.tmweb.ru"
BASE_EXCHANGE_URL = f"{HOST}/webapi/api/flowDiagramm/GetData?"

MAP_GENERATION_1 = {
    "P_AES": "nuclear",
    "P_GES": "hydro",
    "P_GRES": "unknown",
    "P_TES": "unknown",
    "P_BS": "unknown",
    "P_REN": "solar",
    "P_WIND": "wind",
}

MAP_GENERATION_2 = {"aes_gen": "nuclear", "ges_gen": "hydro", "P_tes": "unknown"}

IGNORE_KEYS = {
    "M_DATE",
    "INTERVAL",
    "date",
    "hour",
    "fHour",
    "Pmin_tes",
    "Pmax_tes",
    "power_sys_id",
    "price_zone_id",
}

exchange_ids = {
    "RU-AS->CN": 764,
    "RU->MN": 276,
    "RU-2->MN": 276,
    "RU->KZ": 785,
    "RU-1->KZ": 2394,
    "RU-2->KZ": 344,
    "RU-2->RU-1": 139,
    "RU->GE": 752,
    "RU-1->GE": 752,
    "AZ->RU": 598,
    "AZ->RU-1": 598,
    "BY->RU": 321,
    "BY->RU-1": 321,
    "RU->FI": 187,
    "RU-1->FI": 187,
    "RU-KGD->LT": 212,
    "RU-1->UA-CR": 5688,
    "UA->RU-1": 880,
}

SOURCE = "so-ups.ru"

# Each exchange is contained in a div tag with a "data-id" attribute that is unique.


TIMEZONE = ZoneInfo("Europe/Moscow")


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Fetch production data for Russian zones (1st and 2nd synchronous zones)."""
    session = session or Session()

    # Zone configuration
    zone_key_price_zone_mapper = {
        "RU-1": 1,
        "RU-2": 2,
    }

    # Validate zone
    if zone_key not in zone_key_price_zone_mapper and zone_key != "RU-AS":
        raise NotImplementedError("This parser is not able to parse given zone")

    # Prepare datetime
    if target_datetime:
        target_datetime_tz = target_datetime.astimezone(tz=TIMEZONE)
    else:
        target_datetime_tz = datetime.now(TIMEZONE)
    datetime_to_fetch = target_datetime_tz - timedelta(hours=1)
    date = datetime_to_fetch.strftime("%Y.%m.%d")

    # Build URL based on zone type
    if zone_key in zone_key_price_zone_mapper:
        # 1st synchronous zone (RU-1, RU-2)
        price_zone = zone_key_price_zone_mapper[zone_key]
        url = f"{HOST}/webapi/api/CommonInfo/PowerGeneration?priceZone[]={price_zone}&startDate={date}&endDate={date}"
        generation_map = MAP_GENERATION_1
        date_key = "M_DATE"
        hour_key = "INTERVAL"
    else:
        # 2nd synchronous zone (RU-AS)
        url = f"{HOST}/webapi/api/CommonInfo/GenEquipOptions_Z2?oesTerritory[]=540000&startDate={date}"
        generation_map = MAP_GENERATION_2
        date_key = "date"
        hour_key = "hour"

    response = session.get(url, verify=False)
    json_content = json.loads(response.text)
    dataset = json_content[0]["m_Item2"]

    production_breakdown_list = ProductionBreakdownList(logger=logger)
    for datapoint in dataset:
        production = ProductionMix()

        for key in datapoint:
            if key in IGNORE_KEYS:
                continue
            if key in generation_map:
                production_type = generation_map[key]
                gen_value = datapoint[key]
                production.add_value(
                    mode=production_type,
                    value=gen_value,
                    correct_negative_with_zero=True,
                )
            else:
                logger.warning(
                    f"Unknown production type '{key}' with value {datapoint[key]} in {zone_key} production data"
                )

        # Parse datetime based on zone type
        date = datetime.fromisoformat(datapoint[date_key])
        interval_hour = datapoint[hour_key]

        dt = date + timedelta(hours=interval_hour)

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production,
            source=SOURCE,
        )

    return production_breakdown_list.to_list()


def response_checker(json_content) -> bool:
    flow_values = json_content["Flows"]

    if not flow_values:
        return False

    non_zero = False
    for item in flow_values:
        if item["Id"] in list(exchange_ids.values()):
            if item["NumValue"] == 0.0:
                continue
            else:
                non_zero = True
                break

    return non_zero


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    today = target_datetime if target_datetime else datetime.now(timezone.utc)

    date = today.date().isoformat()
    r = session or Session()
    DATE = f"Date={date}"

    exchange_urls = []
    if target_datetime:
        for hour in range(0, 24):
            url = BASE_EXCHANGE_URL + DATE + f"&Hour={hour}"
            exchange_urls.append((url, hour))
    else:
        # Only fetch last 2 hours when not fetching historical data.
        for shift in range(0, 2):
            hour = (today - timedelta(hours=shift)).strftime("%H")
            url = BASE_EXCHANGE_URL + DATE + f"&Hour={hour}"
            exchange_urls.append((url, int(hour)))

    datapoints = []
    for url, hour in exchange_urls:
        response = r.get(url, verify=False)
        json_content = json.loads(response.text)

        if response_checker(json_content):
            datapoints.append((json_content["Flows"], hour))
        else:
            # data not yet available for this hour
            continue

    sortedcodes = "->".join(sorted([zone_key1, zone_key2]))
    reversesortedcodes = "->".join(sorted([zone_key1, zone_key2], reverse=True))

    if sortedcodes in exchange_ids:
        exchange_id = exchange_ids[sortedcodes]
        direction = 1
    elif reversesortedcodes in exchange_ids:
        exchange_id = exchange_ids[reversesortedcodes]
        direction = -1
    else:
        raise NotImplementedError("This exchange pair is not implemented.")

    data = []
    for datapoint, hour in datapoints:
        try:
            exchange = [item for item in datapoint if item["Id"] == exchange_id][0]
            flow = exchange.get("NumValue") * direction
        except KeyError:
            # flow is unknown or not available
            flow = None

        dt = today.replace(hour=hour, minute=0, second=0, microsecond=0)

        exchange = {
            "sortedZoneKeys": sortedcodes,
            "datetime": dt,
            "netFlow": flow,
            "source": SOURCE,
        }

        data.append(exchange)

    return data
