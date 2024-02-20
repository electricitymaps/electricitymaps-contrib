#!/usr/bin/env python3

import json
import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    ProductionMix,
)
from electricitymap.contrib.lib.types import ZoneKey

# This parser gets hourly electricity generation data from ut.com.sv for El Salvador.
# The 'Termico' category historicallyl only consisted of generation from oil/diesel, but this changed in 2022
# when a new Liquid Natural Gas power plant came online
# See: https://ourworldindata.org/grapher/electricity-prod-source-stacked?country=~SLV
# A better data source that distinguishes between oil and gas can be found in #1733 and #5233

# Thanks to jarek for figuring out how to make the correct POST request to the data url.

DAILY_OPERATION_URL = "https://estadistico.ut.com.sv/OperacionDiaria.aspx"
TIMEZONE = ZoneInfo("America/El_Salvador")
SOURCE = "ut.com.sv"

MODE_MAPPING = {
    "Biomasa": "biomass",
    "Eólico": "wind",
    "Geotérmico": "geothermal",
    "Hidroeléctrico": "hydro",
    "Solar": "solar",
    "Térmico": "unknown",
    "Interconexión": "exchange",
}


def get_data(session: Session) -> Response:
    """
    Makes a get request to data url.
    Parses the response then makes a post request to the same url using
    parsed parameters from the get request.
    Returns a requests response object.
    """
    pagereq = session.get(DAILY_OPERATION_URL)

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

    datareq = session.post(DAILY_OPERATION_URL, data=postdata)

    return datareq


def data_parser(response: Response) -> list[dict]:
    """
    Slices the object down to a smaller size then converts to usable json.
    Loads the data as json then finds the 'result' key.
    Uses regex to find the start
    and endpoints of the actual data.
    Splits the data into datapoints then cleans them up for processing.
    """
    double_json = response.text[len("0|/*DX*/(") : -1]
    double_json = double_json.replace("'", '"')
    double_json = double_json.replace("\\n", "")
    double_json = double_json.replace("\\t", "")
    # Replacing js date objects with isoformat strings.
    JS_DATE_REGEX = re.compile(
        r"new Date\((?P<year>\d*),(?P<month>\d*),(?P<day>\d*),(?P<hour>\d*),(?P<minute>\d*),(?P<second>\d*),(?P<ms>\d*)\)"
    )
    matches = JS_DATE_REGEX.findall(double_json)
    if matches:
        for _match in matches:
            year, month, day, hour, minute, second, ms = _match
            dt = datetime(
                year=int(year),
                month=int(month) + 1,
                day=int(day),
                hour=int(hour),
                tzinfo=TIMEZONE,
            )
            double_json = double_json.replace(
                f"new Date({year},{month},{day},{hour},{minute},{second},{ms})",
                f'\\"{dt.isoformat()}\\"',
            )
    data = json.loads(double_json)
    jsresult = data["result"]
    clean_json = json.loads(jsresult[1:-1])
    datapoints = []
    for item in clean_json["PaneContent"]:
        generation_data = item["ItemData"]["DataStorageDTO"]
        mapping = generation_data["EncodeMaps"]
        if "DataItem3" not in mapping or len(mapping["DataItem3"]) != 1:
            continue
        day = mapping["DataItem3"][0]
        hours = mapping["DataItem1"]
        modes = mapping["DataItem2"]
        slices = generation_data[
            "Slices"
        ]  # Slices are the different reprensentations of the data (hourly totals, hourly breakdowns, daily totals, daily breakdowns)
        hourly_mode_breakdown = list(
            filter(
                lambda x: x["KeyIds"] == ["DataItem2", "DataItem3", "DataItem1"], slices
            )
        )[0]  # We take the hourly breakdown per mode
        for keys, value in hourly_mode_breakdown["Data"].items():
            key_ids = [int(key) for key in keys[1:-1].split(",")]
            mode = modes[key_ids[0]]
            hour = hours[key_ids[2]]
            datapoint = {
                "mode": mode,
                "datetime": datetime.fromisoformat(day).replace(
                    hour=int(hour), tzinfo=TIMEZONE
                ),
                "value": value["0"],
            }
            datapoints.append(datapoint)

    return datapoints


def data_processer(
    zone_key: ZoneKey, data: list[dict], logger: Logger
) -> ProductionBreakdownList:
    """
    Takes data in the form of a list of lists.
    Converts each list to a dictionary.
    Joins dictionaries based on shared datetime key.
    Maps generation to type.
    """
    per_mode_production: dict[str, ProductionBreakdownList] = {}
    filtered_data = filter(
        lambda x: x["mode"] != "Interconexión", data
    )  # TODO: handle interconnection
    for point in filtered_data:
        mode = point["mode"]
        if mode not in per_mode_production:
            per_mode_production[mode] = ProductionBreakdownList(logger)
        mix = ProductionMix()
        mix.add_value(MODE_MAPPING[mode], point["value"])
        per_mode_production[mode].append(
            zoneKey=zone_key, datetime=point["datetime"], source=SOURCE, production=mix
        )

    return ProductionBreakdownList.merge_production_breakdowns(
        list(per_mode_production.values()), logger
    )


def fetch_production(
    zone_key: ZoneKey = ZoneKey("SV"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    if session is None:
        session = Session()
    req = get_data(session)
    parsed = data_parser(req)
    production_breakdown = data_processer(zone_key, parsed, logger)
    return production_breakdown.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
