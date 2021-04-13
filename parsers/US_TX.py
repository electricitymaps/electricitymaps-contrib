"""Parser for the ERCOT area of the United States. (~85% of Texas)"""

import csv
import io
import logging
import zipfile

import arrow
import requests
from lxml import html

from .lib.exceptions import ParserException

# This xpath gets the second cell in a row which has a cell that contains parameterized text
REAL_TIME_DATA_XPATH = "//tr[td[contains(text(),'{}')]]/td[2]/text()"

SOLAR_REAL_TIME_DIRECTORY_URL = (
    "http://mis.ercot.com/misapp/GetReports.do?reportTypeId=13484"
)
WIND_REAL_TIME_DIRECTORY_URL = (
    "http://mis.ercot.com/misapp/GetReports.do?reportTypeId=13071"
)
REAL_TIME_URL = "http://www.ercot.com/content/cdr/html/real_time_system_conditions.html"
BASE_ZIP_URL = "http://mis.ercot.com/"

ELECTRICAL_TIES = ["DC_E", "DC_L", "DC_N", "DC_R", "DC_S"]


def get_zipped_csv_data(logger, directory_url, session=None):
    """Returns 5 minute generation data in json format."""

    s = session or requests.session()
    response = s.get(directory_url)
    if response.status_code != 200 or not response.content:
        raise ParserException(
            "US-TX", "Response code: {0}".format(response.status_code)
        )
    html_tree = html.fromstring(response.content)
    # This xpath gets the first row to contain 'csv' and then the zip link
    most_recent_csv_zip_url = (
        BASE_ZIP_URL
        + html_tree.xpath("//tr[td[contains(text(),'csv')]]/td/div/a/@href")[0]
    )

    response = s.get(most_recent_csv_zip_url)
    if response.status_code != 200 or not response.content:
        raise ParserException(
            "US-TX", "Response code: {0}".format(response.status_code)
        )
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    reader = csv.reader(
        io.StringIO(zip_file.read(zip_file.namelist()[0]).decode("utf-8"))
    )
    next(reader)  # skip header
    row = next(reader)  # only get first row
    return (
        arrow.get(
            arrow.get(row[0], "MM/DD/YYYY HH:mm").datetime, "US/Central"
        ).datetime,
        float(row[1]),
    )


def get_realtime_data(logger, session=None):
    s = session or requests.session()
    response = s.get(REAL_TIME_URL)
    if response.status_code != 200 or not response.content:
        raise ParserException(
            "US-TX", "Response code: {0}".format(response.status_code)
        )
    html_tree = html.fromstring(response.content)

    demand = float(
        html_tree.xpath(REAL_TIME_DATA_XPATH.format("Actual System Demand"))[0]
    )

    tie_dict = {}
    for tie in ELECTRICAL_TIES:
        tie_dict[tie] = float(html_tree.xpath(REAL_TIME_DATA_XPATH.format(tie))[0])

    # This xpath gets the text from the timestamp
    date_string = str(
        html_tree.xpath("//div[contains(@class,'schedTime')]/text()")[0]
    ).replace("Last Updated: ", "")
    return (
        arrow.get(
            arrow.get(date_string, "MMM DD, YYYY HH:mm:ss").datetime, "US/Central"
        ).datetime,
        demand,
        tie_dict,
    )


def fetch_production(
    zone_key="US-TX",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    """
    Requests the last known production mix (in MW) of a given country.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    wind_datetime, wind = get_zipped_csv_data(
        logger, WIND_REAL_TIME_DIRECTORY_URL, session=session
    )
    solar_datetime, solar = get_zipped_csv_data(
        logger, SOLAR_REAL_TIME_DIRECTORY_URL, session=session
    )

    wind_solar_timedelta = (wind_datetime - solar_datetime).total_seconds() / 60
    if (
        abs(wind_solar_timedelta) > 4
    ):  # in case one was grabbed before the other was posted
        if wind_solar_timedelta > 0:  # if solar came earlier, poll it again
            solar_datetime, solar = get_zipped_csv_data(
                logger, SOLAR_REAL_TIME_DIRECTORY_URL, session=session
            )
        else:  # if wind came earlier poll it again
            wind_datetime, wind = get_zipped_csv_data(
                logger, WIND_REAL_TIME_DIRECTORY_URL, session=session
            )

    if solar < 0:
        logger.warn(
            "Solar production for US_TX was reported as less than 0 and was clamped"
        )
        solar = 0.0
    if wind < 0:
        logger.warn(
            "Wind production for US_TX was reported as less than 0 and was clamped"
        )
        wind = 0.0

    realtime_datetime, demand, ties = get_realtime_data(logger, session=session)

    data = {
        "zoneKey": zone_key,
        "datetime": wind_datetime,
        "production": {
            "solar": solar,
            "wind": wind,
            "unknown": demand - solar - wind - sum(ties.values()),
        },
        "storage": {},
        "source": "ercot.com",
    }

    return data


def fetch_consumption(
    zone_key="US-TX",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    """Gets consumption for a specified zone, returns a dictionary."""

    realtime_datetime, demand, ties = get_realtime_data(logger, session=session)

    data = {
        "zoneKey": zone_key,
        "datetime": realtime_datetime,
        "consumption": demand,
        "source": "ercot.eu",
    }

    return data


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
