#!/usr/bin/env python3

"""Parser for the PJM area of the United States."""

import re
from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import demjson3 as demjson
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("America/New_York")

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


def get_api_subscription_key(session: Session) -> str:
    pjm_settings: Response = session.get(
        "https://dataminer2.pjm.com/config/settings.json"
    )
    if pjm_settings.status_code == 200:
        return pjm_settings.json()["subscriptionKey"]
    raise ParserException(
        parser="US_PJM.py",
        message="Could not get API key",
    )


def fetch_api_data(kind: str, params: dict, session: Session) -> list:
    headers = {
        "Host": "api.pjm.com",
        "Ocp-Apim-Subscription-Key": get_api_subscription_key(session=session),
        "Origin": "http://dataminer2.pjm.com",
        "Referer": "http://dataminer2.pjm.com/",
    }
    url = API_ENDPOINT + kind
    resp: Response = session.get(url=url, params=params, headers=headers)
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
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets consumption forecast for specified zone."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    if not session:
        session = Session()

    # startRow must be set if forecast_area is set.
    # RTO_COMBINED is area for whole PJM zone.
    params = {"download": True, "startRow": 1, "forecast_area": "RTO_COMBINED"}

    # query API
    data = fetch_api_data(kind="load_frcstd_7_day", params=params, session=session)

    data_points = []
    for elem in data:
        utc_datetime = elem["forecast_datetime_beginning_utc"]
        data_point = {
            "zoneKey": zone_key,
            "datetime": datetime.fromisoformat(utc_datetime).replace(
                tzinfo=timezone.utc
            ),
            "value": elem["forecast_load_mw"],
            "source": "pjm.com",
        }
        data_points.append(data_point)

    return data_points


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "US-PJM",
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """uses PJM API to get generation  by fuel. we assume that storage is battery storage (see https://learn.pjm.com/energy-innovations/energy-storage)"""
    if target_datetime is None:
        target_datetime = datetime.now(timezone.utc)

    params = {
        "download": True,
        "startRow": 1,
        "fields": "datetime_beginning_ept,fuel_type,mw",
        "datetime_beginning_ept": target_datetime.strftime("%Y-%m-%dT%H:00:00.0000000"),
    }
    resp_data = fetch_api_data(kind="gen_by_fuel", params=params, session=session)

    data = pd.DataFrame(resp_data)
    if not data.empty:
        data["datetime_beginning_ept"] = pd.to_datetime(data["datetime_beginning_ept"])
        data = data.set_index("datetime_beginning_ept")
        data["fuel_type"] = data["fuel_type"].map(FUEL_MAPPING)

        all_data_points = []
        for dt in data.index.unique():
            production = {}
            storage = {}
            data_dt = data.loc[data.index == dt]
            for i in range(len(data_dt)):
                row = data_dt.iloc[i]
                if row["fuel_type"] == "battery":
                    storage["battery"] = row.get("mw")
                else:
                    mode = row["fuel_type"]
                    production[mode] = row.get("mw")
            data_point = {
                "zoneKey": zone_key,
                "datetime": dt.to_pydatetime().replace(tzinfo=TIMEZONE),
                "production": production,
                "storage": storage,
                "source": "pjm.com",
            }
            all_data_points += [data_point]
        return all_data_points
    else:
        raise ParserException(
            parser="US_PJM.py",
            message=f"{target_datetime}: Production data is not available in the API",
        )


def get_miso_exchange(session: Session) -> tuple:
    """
    Current exchange status between PJM and MISO.
    :return: tuple containing flow and timestamp.
    """

    map_url = "http://pjm.com/markets-and-operations/interregional-map.aspx"

    res: Response = session.get(map_url)
    soup = BeautifulSoup(res.text, "html.parser")

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
    dt = parser.parse(find_timestamp.text, tzinfos={"EDT": -4 * 3600, "EST": -5 * 3600})

    return flow, dt


def get_exchange_data(interface, session: Session) -> list:
    """
    This function can fetch 5min data for any PJM interface in the current day.
    Extracts load and timestamp data from html source then joins them together.
    """
    base_url = "http://www.pjm.com/Charts/InterfaceChart.aspx?open="
    url = base_url + exchange_mapping[interface]

    res: Response = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

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

    flows = zip(actual_load, time_vals, strict=True)

    date = datetime.combine(datetime.now(TIMEZONE), time())  # truncate to day

    converted_flows = []
    for flow in flows:
        time_of_the_day = datetime.strptime(
            flow[1],
            "%I:%M %p",  # make sure to use %I and not %H for %p to take effect
        ).replace(tzinfo=TIMEZONE)
        dt = date.replace(hour=time_of_the_day.hour, minute=time_of_the_day.minute)
        converted_flow = (flow[0], dt)
        converted_flows.append(converted_flow)

    return converted_flows


def combine_NY_exchanges(session: Session) -> list:
    """
    Combination function for the 4 New York interfaces.
    Timestamps are checked to ensure correct combination.
    """

    nyiso = get_exchange_data("nyiso", session)
    neptune = get_exchange_data("neptune", session)
    linden = get_exchange_data("linden", session)
    hudson = get_exchange_data("hudson", session)

    combined_flows = zip(nyiso, neptune, linden, hudson, strict=True)

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
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the last known power exchange (in MW) between two zones."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # PJM reports exports as negative.
    sortedcodes = "->".join(sorted([zone_key1, zone_key2]))

    if sortedcodes == "US-NY->US-PJM":
        flows = combine_NY_exchanges(session)
    elif sortedcodes == "US-MIDA-PJM->US-NY-NYIS":
        flows = combine_NY_exchanges(session)
        flows = [(-total, dt) for total, dt in flows]
    elif sortedcodes == "US-MISO->US-PJM":
        flow = get_miso_exchange(session)
        exchange = {
            "sortedZoneKeys": sortedcodes,
            "datetime": flow[1],
            "netFlow": flow[0],
            "source": "pjm.com",
        }
        return exchange
    elif sortedcodes == "US-MIDA-PJM->US-MIDW-MISO":
        flow = get_miso_exchange(session)
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
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power price of a given country."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    res: Response = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    price_tag = soup.find("span", class_="rtolmpico")
    price_data = price_tag.find_next("h2")
    price_string = price_data.text.split("$")[1]
    price = float(price_string)

    dt = datetime.now(TIMEZONE).replace(microsecond=0)  # truncate to seconds

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
