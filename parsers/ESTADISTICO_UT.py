#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    ProductionMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from parsers.lib.config import refetch_frequency

# This parser gets hourly electricity generation data from ut.com.sv for El Salvador.
# The 'Termico' category historically only consisted of generation from oil/diesel, but this changed in 2022
# when a new Liquid Natural Gas power plant came online
# See: https://ourworldindata.org/grapher/electricity-prod-source-stacked?country=~SLV
# A better data source that distinguishes between oil and gas can be found in #1733 and #5233

# Thanks to jarek for figuring out how to make the correct POST request to the data url.

DAILY_OPERATION_URL = "https://estadistico.ut.com.sv/OperacionDiaria.aspx"
SOURCE = "ut.com.sv"
ZONE_INFO = ZoneInfo("America/El_Salvador")

MODE_MAPPING = {
    "Biomasa": "biomass",
    "Eólico": "wind",
    "Geotérmico": "geothermal",
    "Hidroeléctrico": "hydro",
    "Solar": "solar",
    "Térmico": "unknown",
    "Interconexión": "exchange",
}


def _fetch_data(session: Session, target_datetime: datetime | None = None) -> dict:
    """
    Fetches production data from a webpage meant for human eyes rather than
    programmatic access.

    The returned production data is a response meant to be used by a dashboard
    component on the webpage which needs to be parsed further.
    """
    # initial GET request to acquire required state data for POST request
    initial_resp = session.get(DAILY_OPERATION_URL)
    soup = BeautifulSoup(initial_resp.content, "html.parser")

    # define POST request's post data based on
    if not target_datetime:
        date_encoded = "1990-01-01T17%3A32%3A00.000"  # This means live data - I know it is weird but it works
    else:
        date_encoded = (
            target_datetime.strftime("%Y-%m-%d") + "T00%3A00%3A00%2E000"
        )  # This means historical data

    post_data = {
        # dynamically set based on initial request's response
        "__VIEWSTATE": soup.find("input", {"id": "__VIEWSTATE"})["value"],
        "__VIEWSTATEGENERATOR": soup.find("input", {"id": "__VIEWSTATEGENERATOR"})[
            "value"
        ],
        "__EVENTVALIDATION": soup.find("input", {"id": "__EVENTVALIDATION"})["value"],
        # hardcoded based on mimicing requests seen at
        # https://estadistico.ut.com.sv/OperacionDiaria.aspx
        "__CALLBACKID": "ASPxDashboardViewer1",
        "__CALLBACKPARAM": 'c1:{"url":"DXDD.axd?action=DashboardItemBatchGetAction&dashboardId=DashboardID&parameters=%5B%7B%22name%22%3A%22FechaConsulta%22%2C%22value%22%3A%22'
        + date_encoded
        + '%22%2C%22type%22%3A%22System.DateTime%22%2C%22allowMultiselect%22%3Afalse%2C%22selectAll%22%3Afalse%7D%5D&items=%7B%22pivotDashboardItem1%22%3A%7B%7D%2C%22chartDashboardItem1%22%3A%7B%7D%2C%22gridDashboardItem1%22%3A%7B%7D%2C%22gridDashboardItem2%22%3A%7B%7D%2C%22gridDashboardItem3%22%3A%7B%7D%7D","method":"GET","data":""}',
        "DXScript": "1_9,1_10,1_253,1_21,1_62,1_12,1_13,1_0,1_4,24_364,24_365,24_366,24_367,24_359,24_362,24_363,24_360,24_361,24_479,24_480,25_0,24_368,24_440,24_441,15_0,25_2,25_1,25_3",
        "DXCss": "1_72,1_66,24_378,24_379,24_414,24_442,24_443,24_478,15_1",
    }

    data_resp = session.post(DAILY_OPERATION_URL, data=post_data)

    # The text response is expected to look like one of the strings:
    #
    #     0|/*DX*/({'id':1,'result':'{"gridDashboardItem3": {}, "gridDashboardItem2": {}}'})
    #
    #     0|/*DX*/({'error':{'message':'Callback request failed due to an internal server error.'},'result':null,'id':1})
    #
    # Note that:
    # - <content> is wrapped like 0|/*DX*/(<content>)
    # - <content> is JSON like, but using single quotes instead of double quotes
    # - content data can include a result key, and possibly also an error key
    # - the result value is a JSON string
    #
    content_string = data_resp.text[len("0|/*DX*/(") : -len(")")]
    content_json = content_string.replace('"', r"\"").replace("'", '"')
    content_data = json.loads(content_json)
    if content_data.get("error"):
        raise ParserException(
            parser="SV", message=f'Error response returned: {content_data["error"]}'
        )
    data_resp = json.loads(content_data["result"])

    return data_resp


def _parse_data(data: dict) -> list[dict]:
    """
    Parses already fetched data meant for use by a dashboard further into a list
    of dictionaries.
    """
    production_data = data["pivotDashboardItem1"]["ItemData"]["DataStorageDTO"]

    # power production data is available for listed modes, days, and hours
    modes = production_data["EncodeMaps"]["DataItem2"]
    days = production_data["EncodeMaps"]["DataItem3"]
    hours = production_data["EncodeMaps"]["DataItem1"]

    # look at power production data for specific mode, day, and hour
    mode_day_hour_dict = [
        s
        for s in production_data["Slices"]
        if s["KeyIds"] == ["DataItem2", "DataItem3", "DataItem1"]
    ][0]["Data"]

    data_points = []
    for index_values_json, mwh_production_dict in mode_day_hour_dict.items():
        # index_values_json can for example look like "[1,0,1]", which would
        # indicate that its associated with the second mode, first day, and
        # second hour from the available modes, days, and hours
        index_values = json.loads(index_values_json)
        mode = modes[index_values[0]]
        day = days[index_values[1]]
        hour = hours[index_values[2]]

        mwh_production = mwh_production_dict["0"]

        # TODO: Remove the truncation of sub-seconds when we run on Python 3.11
        #       or above and fromisoformat can parse such strings
        day = day[: day.find(".")]
        dt = datetime.fromisoformat(day).replace(hour=int(hour), tzinfo=ZONE_INFO)

        data_points.append(
            {
                "mode": MODE_MAPPING[mode],
                "datetime": dt,
                "value": mwh_production,
            }
        )
    return data_points


def _process_data(
    zone_key: ZoneKey, data: list[dict], logger: Logger
) -> ProductionBreakdownList:
    # ignore collected exchange data for now
    data = [d for d in data if d["mode"] != "exchange"]

    per_mode_production: dict[str, ProductionBreakdownList] = {}
    for d in data:
        mode = d["mode"]
        if mode not in per_mode_production:
            per_mode_production[mode] = ProductionBreakdownList(logger)

        mix = ProductionMix()
        mix.add_value(mode, d["value"])
        per_mode_production[mode].append(
            datetime=d["datetime"],
            production=mix,
            zoneKey=zone_key,
            source=SOURCE,
        )

    return ProductionBreakdownList.merge_production_breakdowns(
        list(per_mode_production.values()),
        logger,
    )


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("SV"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if session is None:
        session = Session()

    data = _fetch_data(session, target_datetime)
    parsed_data = _parse_data(data)
    production_breakdown = _process_data(zone_key, parsed_data, logger)
    return production_breakdown.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
