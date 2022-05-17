#!/usr/bin/env python3

import logging
import xml.etree.ElementTree as ET
from datetime import timedelta, timezone

# The arrow library is used to handle datetimes
import arrow

# pandas processes tabular data
import pandas as pd

# The request library is used to fetch content through HTTP
import requests

"""
Some notes about timestamps:

IESO website says:
"The IESO uses the "Hour Ending" naming convention for the hours in a day. For example, Hour 1 is from 12 am. to 1 am.,
Hour 2 is from 1 am. to 2 am. Hours 1-24 are the hours from midnight one day through midnight the next day."

Observations:
- At 13:53, HOEP report will have data with "Hour" column from 1 to 13.
  Output and Capability report will have data with "Hour" column from 1 to 13.
  Intertie Flow report will have data with "Hour" column from 1 to 13 *and* Interval column
  from 1 to 12 for all of these hours, including the 13th hour.
- At 14:18, HOEP report will go up to 14, Output report will go up to 14,
  but update for Intertie report is not yet updated.
- At 14:31, Intertie report is updated with Hour 14 which has Intervals 1 to 12.

In the script, the Intertie report is shifted 1 hour and 5 minutes back, so that it lines up with
the production and price data availability.
"""

# IESO says "Eastern Standard Time is used year round."
# This would mean daylight savings is not used (that is called "Eastern Daylight Time"),
# and we need to use UTC-5 rather than 'Canada/Eastern'
tz_obj = timezone(timedelta(hours=-5), name="UTC-5")

# fuel types used by IESO
MAP_GENERATION = {
    "BIOFUEL": "biomass",
    "GAS": "gas",
    "HYDRO": "hydro",
    "NUCLEAR": "nuclear",
    "SOLAR": "solar",
    "WIND": "wind",
}

# exchanges and sub-exchanges used by IESO
MAP_EXCHANGE = {
    "MANITOBA": "CA-MB->CA-ON",
    "MANITOBA SK": "CA-MB->CA-ON",
    "MICHIGAN": "CA-ON->US-MIDW-MISO",
    "MINNESOTA": "CA-ON->US-MIDW-MISO",
    "NEW-YORK": "CA-ON->US-NY-NYIS",
    "PQ.AT": "CA-ON->CA-QC",
    "PQ.B5D.B31L": "CA-ON->CA-QC",
    "PQ.D4Z": "CA-ON->CA-QC",
    "PQ.D5A": "CA-ON->CA-QC",
    "PQ.H4Z": "CA-ON->CA-QC",
    "PQ.H9A": "CA-ON->CA-QC",
    "PQ.P33C": "CA-ON->CA-QC",
    "PQ.Q4C": "CA-ON->CA-QC",
    "PQ.X2Y": "CA-ON->CA-QC",
}

PRODUCTION_URL = "http://reports.ieso.ca/public/GenOutputCapability/PUB_GenOutputCapability_{YYYYMMDD}.xml"
PRICE_URL = (
    "http://reports.ieso.ca/public/DispUnconsHOEP/PUB_DispUnconsHOEP_{YYYYMMDD}.xml"
)
EXCHANGES_URL = "http://reports.ieso.ca/public/IntertieScheduleFlow/PUB_IntertieScheduleFlow_{YYYYMMDD}.xml"

XML_NS_TEXT = "{http://www.theIMO.com/schema}"


def _fetch_ieso_xml(target_datetime, session, logger, url_template):
    dt = (
        arrow.get(target_datetime)
        .to(tz_obj)
        .replace(hour=0, minute=0, second=0, microsecond=0)
    )

    r = session or requests.session()
    url = url_template.format(YYYYMMDD=dt.format("YYYYMMDD"))
    response = r.get(url)

    if not response.ok:
        # Data is generally available for past 3 months. Requesting files older than this
        # returns an HTTP 404 error.
        logger.info(
            "CA-ON: failed getting requested data for datetime {} from IESO server - URL {}".format(
                dt, url
            )
        )
        return dt, None

    xml = ET.fromstring(response.text)

    return dt, xml


def _parse_ieso_hour(output, target_dt):
    hour = int(output.find(XML_NS_TEXT + "Hour").text)
    return target_dt.shift(hours=hour).datetime


def fetch_production(
    zone_key="CA-ON",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given region."""

    dt, xml = _fetch_ieso_xml(target_datetime, session, logger, PRODUCTION_URL)

    if not xml:
        return []

    generators = (
        xml.find(XML_NS_TEXT + "IMODocBody")
        .find(XML_NS_TEXT + "Generators")
        .findall(XML_NS_TEXT + "Generator")
    )

    def production_or_zero(output):
        # Sometimes the XML data has no "EnergyMW" tag for a given plant at a given hour.
        # The report XSL formats this as "N/A" - we return 0
        tag = output.find(XML_NS_TEXT + "EnergyMW")
        if tag is not None:
            return tag.text
        else:
            return 0

    # flat iterable of per-generator-plant productions per time from the XML data
    all_productions = (
        {
            "name": generator.find(XML_NS_TEXT + "GeneratorName").text,
            "fuel": MAP_GENERATION[generator.find(XML_NS_TEXT + "FuelType").text],
            "dt": _parse_ieso_hour(output, dt),
            "production": float(production_or_zero(output)),
        }
        for generator in generators
        for output in generator.find(XML_NS_TEXT + "Outputs").findall(
            XML_NS_TEXT + "Output"
        )
    )

    df = pd.DataFrame(all_productions)

    # group individual plants using the same fuel together for each time period
    by_fuel = df.groupby(["dt", "fuel"]).sum().unstack()
    # to debug, you can `print(by_fuel)` here, which gives a very pretty table

    by_fuel_dict = by_fuel["production"].to_dict("index")

    data = [
        {
            "datetime": time.to_pydatetime(),
            "zoneKey": zone_key,
            "production": productions,
            "storage": {},
            "source": "ieso.ca",
        }
        for time, productions in by_fuel_dict.items()
    ]

    # being constructed from a dict, data is not guaranteed to be in chronological order.
    # sort it for clean-ness and easier debugging.
    data = sorted(data, key=lambda dp: dp["datetime"])

    return data


def fetch_price(
    zone_key="CA-ON",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known power price per MWh of a given region."""

    # "HOEP" below is "Hourly Ontario Energy Price".
    # There also exists a 5-minute price, but its archives only go back roughly 4 days
    # (see http://www.ieso.ca/power-data "5 Minute Market Clearing Price").

    dt, xml = _fetch_ieso_xml(target_datetime, session, logger, PRICE_URL)

    if not xml:
        return []

    prices = (
        xml.find(XML_NS_TEXT + "IMODocBody")
        .find(XML_NS_TEXT + "HOEPs")
        .findall(XML_NS_TEXT + "HOEP")
    )

    data = [
        {
            "datetime": _parse_ieso_hour(price, dt),
            "price": float(price.find(XML_NS_TEXT + "Price").text),
            "currency": "CAD",
            "source": "ieso.ca",
            "zoneKey": zone_key,
        }
        for price in prices
    ]

    return data


def fetch_exchange(
    zone_key1,
    zone_key2,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Requests the last known power exchange (in MW) between two regions."""

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys not in MAP_EXCHANGE.values():
        raise NotImplementedError("This exchange pair is not implemented")

    dt, xml = _fetch_ieso_xml(target_datetime, session, logger, EXCHANGES_URL)

    if not xml:
        return []

    intertie_zones = xml.find(XML_NS_TEXT + "IMODocBody").findall(
        XML_NS_TEXT + "IntertieZone"
    )

    def flow_dt(flow):
        # The IESO day starts with Hour 1, Interval 1.
        # At 11:37, we might have data for up to Hour 11, Interval 12.
        # This means it is necessary to subtract 1 from the values
        # (otherwise we would have data for 12:00 already at 11:37).
        hour = int(flow.find(XML_NS_TEXT + "Hour").text) - 1
        minute = (int(flow.find(XML_NS_TEXT + "Interval").text) - 1) * 5

        return dt.replace(hour=hour, minute=minute).datetime

    # flat iterable of per-intertie values per time from the XML data
    all_exchanges = (
        {
            "name": intertie.find(XML_NS_TEXT + "IntertieZoneName").text,
            "dt": flow_dt(flow),
            "flow": float(flow.find(XML_NS_TEXT + "Flow").text),
        }
        for intertie in intertie_zones
        for flow in intertie.find(XML_NS_TEXT + "Actuals").findall(
            XML_NS_TEXT + "Actual"
        )
    )

    df = pd.DataFrame(all_exchanges)

    # verify that there haven't been new exchanges or sub-exchanges added
    all_exchange_names = set(df["name"].unique())
    known_exchange_names = set(MAP_EXCHANGE.keys())
    unknown_exchange_names = all_exchange_names - known_exchange_names
    if unknown_exchange_names:
        logger.warning(
            "CA-ON: unrecognized intertie name(s) {}, please implement!".format(
                unknown_exchange_names
            )
        )

    # filter to only the sought exchanges
    sought_exchanges = [
        ieso_name
        for ieso_name, em_name in MAP_EXCHANGE.items()
        if sorted_zone_keys == em_name
    ]
    df = df[df["name"].isin(sought_exchanges)]

    # in the XML, flow into Ontario is always negative.
    # in EM, for 'CA-MB->CA-ON', flow into Ontario is positive.
    if not sorted_zone_keys.startswith("CA-ON->"):
        df["flow"] *= -1

    # group flows for sub-interchanges together and sum them
    grouped = df.groupby(["dt"]).sum()

    grouped_dict = grouped["flow"].to_dict()

    data = [
        {
            "datetime": flow_dt.to_pydatetime(),
            "sortedZoneKeys": sorted_zone_keys,
            "netFlow": flow,
            "source": "ieso.ca",
        }
        for flow_dt, flow in grouped_dict.items()
    ]

    # being constructed from a dict, data is not guaranteed to be in chronological order.
    # sort it for clean-ness and easier debugging.
    data = sorted(data, key=lambda dp: dp["datetime"])

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    now = arrow.utcnow()

    print("fetch_production() ->")
    print(fetch_production())

    print("we expect correct results when time in UTC and Ontario differs")
    print(
        "data should be for {}".format(
            now.replace(hour=2).to(tz_obj).format("YYYY-MM-DD")
        )
    )
    print('fetch_production("CA-ON", target_datetime=now.replace(hour=2)) ->')
    print(fetch_production("CA-ON", target_datetime=now.replace(hour=2)))

    print("we expect results for 2 months ago")
    print("fetch_production(target_datetime=now.shift(months=-2).datetime)) ->")
    print(fetch_production(target_datetime=now.shift(months=-2).datetime))

    print("there are likely no results for 2 years ago")
    print("fetch_production(target_datetime=now.shift(years=-2).datetime)) ->")
    print(fetch_production(target_datetime=now.shift(years=-2).datetime))

    print("fetch_price() ->")
    print(fetch_price())

    print("we expect correct results when time in UTC and Ontario differs")
    print(
        "data should be for {}".format(
            now.replace(hour=2).to(tz_obj).format("YYYY-MM-DD")
        )
    )
    print("fetch_price(target_datetime=now.replace(hour=2)) ->")
    print(fetch_price(target_datetime=now.replace(hour=2)))

    print("we expect results for 2 months ago")
    print("fetch_price(target_datetime=now.shift(months=-2).datetime)) ->")
    print(fetch_price(target_datetime=now.shift(months=-2).datetime))

    print("there are likely no results for 2 years ago")
    print("fetch_price(target_datetime=now.shift(years=-2).datetime)) ->")
    print(fetch_price(target_datetime=now.shift(years=-2).datetime))

    print('fetch_exchange("CA-ON", "US-NY") ->')
    print(fetch_exchange("CA-ON", "US-NY"))

    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now.datetime)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now.datetime))

    print(
        "test Ontario-to-Manitoba, this must be opposite sign from reported IESO values"
    )
    print('fetch_exchange("CA-ON", "CA-MB", target_datetime=now.datetime)) ->')
    print(fetch_exchange("CA-ON", "CA-MB", target_datetime=now.datetime))

    print("we expect correct results when time in UTC and Ontario differs")
    print(
        "data should be for {}".format(
            now.replace(hour=2).to(tz_obj).format("YYYY-MM-DD")
        )
    )
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now.replace(hour=2)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now.replace(hour=2)))

    print("we expect results for 2 months ago")
    print(
        'fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(months=-2).datetime)) ->'
    )
    print(
        fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(months=-2).datetime)
    )

    print("there are likely no results for 2 years ago")
    print(
        'fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(years=-2).datetime)) ->'
    )
    print(
        fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(years=-2).datetime)
    )

    print("requesting an exchange with Nova Scotia should raise exception")
    print('fetch_exchange("CA-ON", "CA-NS")) ->')
    print(fetch_exchange("CA-ON", "CA-NS"))
