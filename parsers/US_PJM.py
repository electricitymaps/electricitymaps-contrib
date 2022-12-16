#!/usr/bin/env python3

"""Parser for the PJM area of the United States."""

import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional, Union

import arrow
import demjson3 as demjson
import pandas as pd
import pytz
from bs4 import BeautifulSoup
from dateutil import parser, tz
from requests import Session, Response

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException
from parsers.lib.utils import get_token

# Used for consumption forecast data.
API_ENDPOINT = "https://api.pjm.com/api/v1/"
# Used for both production and price data.
url = "http://www.pjm.com/markets-and-operations.aspx"

mapping = {
    "Coal": "coal",
    "Gas": "gas",
    "Hydro": "hydro",
    "Multiple Fuels": "unknown",
    "Nuclear": "nuclear",
    "Oil": "oil",
    "Other": "unknown",
    "Other Renewables": "unknown",
    "Solar": "solar",
    "Wind": "wind",
}

exchange_mapping = {
    "nyiso": "NYIS|NYIS",
    "neptune": "NEPTUNE|SAYR",
    "linden": "LINDENVFT|LINDEN",
    "hudson": "HUDSONTP|HTP",
    "miso": "miso",
    "ohio valley": "DEOK|OVEC",
    "louisville": "SOUTHIMP|LGEE",
    "tennessee valley": "SOUTHIMP|TVA",
    "cpl west": "SOUTHIMP|CPLW",
    "duke": "SOUTHIMP|DUKE",
    "cpl east": "SOUTHIMP|CPLE",
}

FUEL_MAPPING = {
    "Coal": "coal",
    "Gas": "gas",
    "Hydro": "hydro",
    "Multiple Fuels": "unknown",
    "Nuclear": "nuclear",
    "Oil": "oil",
    "Other": "unknown",
    "Other Renewables": "unknown",
    "Solar": "solar",
    "Storage": "battery",
    "Wind": "wind",
}


def fetch_api_data(kind: str, params: dict, session: Session) -> list:

    headers = {
        "Host": "api.pjm.com",
        "Ocp-Apim-Subscription-Key": get_token("PJM_TOKEN"),
        "Origin": "http://dataminer2.pjm.com",
        "Referer": "http://dataminer2.pjm.com/",
    }
    url = API_ENDPOINT + kind
    resp: Response = session.get(url, params, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return data
    else:
        raise ParserException(
            parser="US_PJM.py",
            message=f"{kind} data is not available in the API",
        )


def fetch_consumption_forecast_7_days(
    zone_key: str = "US-PJM",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets consumption forecast for specified zone."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    if not session:
        session = Session()

    headers = {"Ocp-Apim-Subscription-Key": get_token("PJM_TOKEN")}

    # startRow must be set if forecast_area is set.
    # RTO_COMBINED is area for whole PJM zone.
    params = {"download": True, "startRow": 1, "forecast_area": "RTO_COMBINED"}

    # query API
    data = fetch_api_data(kind="load_frcstd_7_day", params=params, session=session)

    data_points = list()
    for elem in data:
        utc_datetime = elem["forecast_datetime_beginning_utc"]
        data_point = {
            "zoneKey": zone_key,
            "datetime": arrow.get(utc_datetime).replace(tzinfo="UTC").datetime,
            "value": elem["forecast_load_mw"],
            "source": "pjm.com",
        }
        data_points.append(data_point)

    return data_points


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "US-PJM",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """uses PJM API to get generation  by fuel. we assume that storage is battery storage (see https://learn.pjm.com/energy-innovations/energy-storage)"""
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
    if not session:
        session = Session()

    params = {
        "download": True,
        "startRow": 1,
        "fields": "datetime_beginning_ept,fuel_type,mw",
        "datetime_beginning_ept": target_datetime.strftime("%Y-%m-%dT%H:00:00.0000000"),
    }
    resp_data = fetch_api_data(kind="gen_by_fuel", params=params)

    data = pd.DataFrame(resp_data)
    data.fuel_type = data.fuel_type.map(FUEL_MAPPING)

    all_data_points = []
    for dt in set(data.datetime_beginning_ept):
        production = {}
        storage = {}
        data_dt = data.loc[data.datetime_beginning_ept == dt]
        for mode in set(data.fuel_type):
            if mode == "battery":
                storage["battery"] = data_dt.loc[
                    data_dt.fuel_type == mode, "mw"
                ].values[0]
            else:
                production[mode] = data_dt.loc[data_dt.fuel_type == mode, "mw"].values[
                    0
                ]
        data_point = {
            "zoneKey": zone_key,
            "datetime": arrow.get(dt).datetime.replace(
                tzinfo=pytz.timezone("US/Eastern")
            ),
            "production": production,
            "storage": storage,
            "source": "pjm.com",
        }
        all_data_points += [data_point]
    return all_data_points


def add_default_tz(timestamp):
    """Adds EST timezone to datetime object if tz = None."""

    EST = tz.gettz("America/New_York")
    modified_timestamp = timestamp.replace(tzinfo=timestamp.tzinfo or EST)

    return modified_timestamp


def get_miso_exchange(session: Optional[Session] = None) -> tuple:
    """
    Current exchange status between PJM and MISO.
    :return: tuple containing flow and timestamp.
    """

    map_url = "http://pjm.com/markets-and-operations/interregional-map.aspx"

    s = session or Session()
    req = s.get(map_url)
    soup = BeautifulSoup(req.content, "html.parser")

    find_div = soup.find("div", {"id": "body_0_flow1", "class": "flow"})

    miso_flow = find_div.text
    miso_flow_no_ws = "".join(miso_flow.split())
    miso_actual = miso_flow_no_ws.split("/")[0].replace(",", "")
    direction_tag = find_div.find("img")
    left_or_right = direction_tag["src"]

    # The flow direction is determined by img arrows.
    if left_or_right == "/assets/images/mapImages/black-L.png":
        # left set negative
        flow = -1 * float(miso_actual)
    elif left_or_right == "/assets/images/mapImages/black-R.png":
        # right set positive
        flow = float(miso_actual)
    else:
        raise ValueError("US-MISO->US-PJM flow direction cannot be determined.")

    find_timestamp = soup.find("div", {"id": "body_0_divTimeStamp"})
    dt_naive = parser.parse(find_timestamp.text)
    dt_aware = add_default_tz(dt_naive)

    return flow, dt_aware


def get_exchange_data(interface, session: Optional[Session] = None) -> list:
    """
    This function can fetch 5min data for any PJM interface in the current day.
    Extracts load and timestamp data from html source then joins them together.
    """

    base_url = "http://www.pjm.com/Charts/InterfaceChart.aspx?open="
    url = base_url + exchange_mapping[interface]

    s = session or Session()
    req = s.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    scripts = soup.find(
        "script",
        {
            "type": "text/javascript",
            "src": "/assets/js/Highcharts/HighCharts/highcharts.js",
        },
    )

    exchange_script = scripts.find_next_sibling("script")

    load_pattern = r"var load = (\[(.*)\])"
    load = re.search(load_pattern, str(exchange_script)).group(1)
    load_vals = demjson.decode(load)[0]

    # Occasionally load_vals contains a null at the end of the list which must be caught.
    actual_load = [float(val) for val in load_vals if val is not None]

    time_pattern = r"var timeArray = (\[(.*)\])"
    time_array = re.search(time_pattern, str(exchange_script)).group(1)
    time_vals = demjson.decode(time_array)

    flows = zip(actual_load, time_vals)

    arr_date = arrow.now("America/New_York").floor("day")

    converted_flows = []
    for flow in flows:
        arr_time = arrow.get(flow[1], "h:mm A")
        arr_dt = arr_date.replace(hour=arr_time.hour, minute=arr_time.minute).datetime
        converted_flow = (flow[0], arr_dt)
        converted_flows.append(converted_flow)

    return converted_flows


def combine_NY_exchanges() -> list:
    """
    Combination function for the 4 New York interfaces.
    Timestamps are checked to ensure correct combination.
    """

    nyiso = get_exchange_data("nyiso", session=None)
    neptune = get_exchange_data("neptune", session=None)
    linden = get_exchange_data("linden", session=None)
    hudson = get_exchange_data("hudson", session=None)

    combined_flows = zip(nyiso, neptune, linden, hudson)

    flows = []
    for datapoint in combined_flows:
        total = sum([n[0] for n in datapoint])
        stamps = [n[1] for n in datapoint]

        # Data quality check to make sure timestamps all match.
        if len(set(stamps)) == 1:
            dt = stamps[0]
        else:
            # Drop bad datapoint and move to next.
            continue

        flows.append((total, dt))

    return flows


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    """Requests the last known power exchange (in MW) between two zones."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # PJM reports exports as negative.
    sortedcodes = "->".join(sorted([zone_key1, zone_key2]))

    if sortedcodes == "US-NY->US-PJM":
        flows = combine_NY_exchanges()
    elif sortedcodes == "US-MIDA-PJM->US-NY-NYIS":
        flows = combine_NY_exchanges()
        flows = [(-total, dt) for total, dt in flows]
    elif sortedcodes == "US-MISO->US-PJM":
        flow = get_miso_exchange()
        exchange = {
            "sortedZoneKeys": sortedcodes,
            "datetime": flow[1],
            "netFlow": flow[0],
            "source": "pjm.com",
        }
        return exchange
    elif sortedcodes == "US-MIDA-PJM->US-MIDW-MISO":
        flow = get_miso_exchange()
        exchange = {
            "sortedZoneKeys": sortedcodes,
            "datetime": flow[1],
            "netFlow": -flow[0],
            "source": "pjm.com",
        }
        return exchange
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    exchanges = []
    for flow in flows:
        exchange = {
            "sortedZoneKeys": sortedcodes,
            "datetime": flow[1],
            "netFlow": flow[0],
            "source": "pjm.com",
        }
        exchanges.append(exchange)

    return exchanges


def fetch_price(
    zone_key: str = "US-PJM",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power price of a given country."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    s = session or Session()
    req = s.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    price_tag = soup.find("span", class_="rtolmpico")
    price_data = price_tag.find_next("h2")
    price_string = price_data.text.split("$")[1]
    price = float(price_string)

    dt = arrow.now("America/New_York").floor("second").datetime

    data = {
        "zoneKey": zone_key,
        "currency": "USD",
        "datetime": dt,
        "price": price,
        "source": "pjm.com",
    }

    return data


if __name__ == "__main__":
    print("fetch_consumption_forecast_7_days() ->")
    print(fetch_consumption_forecast_7_days())
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(US-NY, US-PJM) ->")
    print(fetch_exchange("US-NY", "US-PJM"))
    print("fetch_exchange(US-MISO, US-PJM)")
    print(fetch_exchange("US-MISO", "US-PJM"))
    print("fetch_price() ->")
    print(fetch_price())
