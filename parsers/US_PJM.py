#!/usr/bin/env python3

"""Parser for the PJM area of the United States."""

import json
import re

import arrow
import demjson3 as demjson
import requests
from bs4 import BeautifulSoup
from dateutil import parser, tz

from .lib.utils import get_token

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


def extract_data(session=None) -> tuple:
    """
    Makes a request to the PJM data url.
    Finds timestamp of current data and converts into a useful form.
    Finds generation data inside script tag.

    :return: tuple of generation data and datetime.
    """

    s = session or requests.Session()
    req = requests.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    try:
        time_div = soup.find("div", id="asOfDate").text
    except AttributeError:
        raise LookupError("No data is available for US-PJM.")

    time_pattern = re.compile(
        r"""(\d{1,2}     #Hour can be 1/2 digits.
                                   :           #Separator.
                                   \d{2})\s    #Minutes must be 2 digits with a space after.
                                   (a.m.|p.m.) #Either am or pm allowed.""",
        re.X,
    )

    latest_time = re.search(time_pattern, time_div)

    time_data = latest_time.group(1).split(":")
    am_or_pm = latest_time.group(2)
    hour = int(time_data[0])
    minute = int(time_data[1])

    # Time format used by PJM is slightly unusual and needs to be converted so arrow can use it.
    if am_or_pm == "p.m." and hour != 12:
        # Time needs to be in 24hr format
        hour += 12
    elif am_or_pm == "a.m." and hour == 12:
        # Midnight is 12 a.m.
        hour = 0

    arr_dt = arrow.now("America/New_York").replace(hour=hour, minute=minute)
    future_check = arrow.now("America/New_York")

    if arr_dt > future_check:
        # Generation mix lags 1-2hrs behind present.
        # This check prevents data near midnight being given the wrong date.
        arr_dt = arr_dt.shift(days=-1)

    dt = arr_dt.floor("minute").datetime

    generation_mix_div = soup.find("div", id="rtschartallfuelspjmGenFuelM_container")
    generation_mix_script = generation_mix_div.next_sibling

    pattern = r"series: \[(.*)\]"
    script_data = re.search(pattern, str(generation_mix_script)).group(1)

    # demjson is required because script data is javascript not valid json.
    raw_data = demjson.decode(script_data)
    data = raw_data["data"]

    return data, dt


def data_processer(data) -> dict:
    """Takes a list of dictionaries and extracts generation type and value from each."""

    production = {}
    for point in data:
        gen_type = mapping[point["name"]]
        gen_value = float(point["y"])
        production[gen_type] = production.get(gen_type, 0.0) + gen_value

    return production


def fetch_consumption_forecast_7_days(
    zone_key="US-PJM", session=None, target_datetime=None, logger=None
) -> list:
    """Gets consumption forecast for specified zone."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    if not session:
        session = requests.session()

    headers = {"Ocp-Apim-Subscription-Key": get_token("PJM_TOKEN")}

    # startRow must be set if forecast_area is set.
    # RTO_COMBINED is area for whole PJM zone.
    params = {"download": True, "startRow": 1, "forecast_area": "RTO_COMBINED"}

    # query API
    url = API_ENDPOINT + "load_frcstd_7_day"
    resp = requests.get(url, params, headers=headers)
    data = json.loads(resp.content)

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


def fetch_production(
    zone_key="US-PJM", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    extracted = extract_data(session=None)
    production = data_processer(extracted[0])

    datapoint = {
        "zoneKey": zone_key,
        "datetime": extracted[1],
        "production": production,
        "storage": {"hydro": None, "battery": None},
        "source": "pjm.com",
    }

    return datapoint


def add_default_tz(timestamp):
    """Adds EST timezone to datetime object if tz = None."""

    EST = tz.gettz("America/New_York")
    modified_timestamp = timestamp.replace(tzinfo=timestamp.tzinfo or EST)

    return modified_timestamp


def get_miso_exchange(session=None) -> tuple:
    """
    Current exchange status between PJM and MISO.
    :return: tuple containing flow and timestamp.
    """

    map_url = "http://pjm.com/markets-and-operations/interregional-map.aspx"

    s = session or requests.Session()
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


def get_exchange_data(interface, session=None) -> list:
    """
    This function can fetch 5min data for any PJM interface in the current day.
    Extracts load and timestamp data from html source then joins them together.
    """

    base_url = "http://www.pjm.com/Charts/InterfaceChart.aspx?open="
    url = base_url + exchange_mapping[interface]

    s = session or requests.Session()
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
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> list:
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
    zone_key="US-PJM", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power price of a given country."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    s = session or requests.Session()
    req = requests.get(url)
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
