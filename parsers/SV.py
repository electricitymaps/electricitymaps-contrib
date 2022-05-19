#!/usr/bin/env python3

import json
import re
from collections import defaultdict
from operator import itemgetter

import arrow
import requests
from bs4 import BeautifulSoup

# This parser gets hourly electricity generation data from ut.com.sv for El Salvador.
# El Salvador does have wind generation but there is no data available.
# The 'Termico' category only consists of generation from oil/diesel according to historical data.
# See: https://www.iea.org/statistics/?country=ELSALVADOR&year=2016&category=Key%20indicators&indicator=ElecGenByFuel
# A new Liquid Natural Gas power plant may come online in 2020/2021.
# See: https://gastechinsights.com/article/what-energa-del-pacficos-lng-to-power-project-means-for-el-salvador

# Thanks to jarek for figuring out how to make the correct POST request to the data url.

url = "http://estadistico.ut.com.sv/OperacionDiaria.aspx"

generation_map = {
    0: "biomass",
    1: "wind",
    2: "geothermal",
    3: "hydro",
    4: "interconnection",
    5: "thermal",
    6: "solar",
    "datetime": "datetime",
}


def get_data(session=None):
    """
    Makes a get request to data url.
    Parses the response then makes a post request to the same url using
    parsed parameters from the get request.
    Returns a requests response object.
    """

    s = session or requests.Session()
    pagereq = s.get(url)

    soup = BeautifulSoup(pagereq.content, "html.parser")

    # Find and define parameters needed to send a POST request for the actual data.
    viewstategenerator = soup.find("input", attrs={"id": "__VIEWSTATEGENERATOR"})[
        "value"
    ]
    viewstate = soup.find("input", attrs={"id": "__VIEWSTATE"})["value"]
    eventvalidation = soup.find("input", attrs={"id": "__EVENTVALIDATION"})["value"]
    DXCss = "1_33,1_4,1_9,1_5,15_2,15_4"
    DXScript = "1_232,1_134,1_225,1_169,1_187,15_1,1_183,1_182,1_140,1_147,1_148,1_142,1_141,1_143,1_144,1_145,1_146,15_0,15_6,15_7"
    callback_param_init = 'c0:{"Task":"Initialize","DashboardId":"OperacionDiaria","Settings":{"calculateHiddenTotals":false},"RequestMarker":0,"ClientState":{}}'

    postdata = {
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategenerator,
        "__EVENTVALIDATION": eventvalidation,
        "__CALLBACKPARAM": callback_param_init,
        "__CALLBACKID": "ASPxDashboardViewer1",
        "DXScript": DXScript,
        "DXCss": DXCss,
    }

    datareq = s.post(url, data=postdata)

    return datareq


def data_parser(datareq) -> list:
    """
    Accepts a requests response.text object.
    Slices the object down to a smaller size then converts to usable json.
    Loads the data as json then finds the 'result' key.
    Uses regex to find the start
    and endpoints of the actual data.
    Splits the data into datapoints then cleans them up for processing.
    """

    double_json = datareq.text[len("0|/*DX*/(") : -1]
    double_json = double_json.replace("'", '"')
    data = json.loads(double_json)
    jsresult = data["result"]

    startpoints = [m.end(0) for m in re.finditer('"Data":{', jsresult)]
    endpoints = [m.start(0) for m in re.finditer('"KeyIds"', jsresult)]

    sliced = jsresult[startpoints[1] : endpoints[2]]
    sliced = "".join(sliced.split())
    sliced = sliced[1:-4]

    chopped = sliced.split(',"')

    diced = []
    for item in chopped:
        item = item.replace("}", "")
        np = item.split('":')
        diced.append(np[0::2])

    clean_data = []
    for item in diced:
        j = json.loads(item[0])
        k = float(item[1])
        j.append(k)
        clean_data.append(j)

    return clean_data


def data_processer(data) -> list:
    """
    Takes data in the form of a list of lists.
    Converts each list to a dictionary.
    Joins dictionaries based on shared datetime key.
    Maps generation to type.
    """

    converted = []
    for val in data:
        newval = {"datetime": val[2], val[0]: val[3]}
        converted.append(newval)

    # Join dicts on 'datetime' key.
    d = defaultdict(dict)
    for elem in converted:
        d[elem["datetime"]].update(elem)

    joined_data = sorted(d.values(), key=itemgetter("datetime"))

    def get_datetime(hour):
        at = arrow.now("UTC-6").floor("hour")
        dt = (at.replace(hour=int(hour), minute=0, second=0)).datetime
        return dt

    mapped_data = []
    for point in joined_data:
        point = {generation_map[num]: val for num, val in point.items()}
        point["datetime"] = get_datetime(point["datetime"])
        mapped_data.append(point)

    return mapped_data


def fetch_production(
    zone_key="SV", session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    req = get_data(session=None)
    parsed = data_parser(req)
    data = data_processer(parsed)
    production_mix_by_hour = []
    for hour in data:
        production_mix = {
            "zoneKey": zone_key,
            "datetime": hour["datetime"],
            "production": {
                "biomass": hour.get("biomass", 0.0),
                "coal": 0.0,
                "gas": 0.0,
                "hydro": hour.get("hydro", 0.0),
                "nuclear": 0.0,
                "oil": hour.get("thermal", 0.0),
                "solar": hour.get("solar", 0.0),
                "wind": hour.get("wind", 0.0),
                "geothermal": hour.get("geothermal", 0.0),
                "unknown": 0.0,
            },
            "storage": {
                "hydro": None,
            },
            "source": "ut.com.sv",
        }
        production_mix_by_hour.append(production_mix)

    return production_mix_by_hour


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
