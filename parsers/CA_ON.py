#!/usr/bin/env python3
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from logging import Logger, getLogger
from typing import Any
from xml.etree import ElementTree

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

# Some notes about timestamps:
#
# The IESO website says:
#
#   The IESO uses the "Hour Ending" naming convention for the hours in a day.
#   For example, Hour 1 is from 12 am. to 1 am., Hour 2 is from 1 am. to 2 am.
#   Hours 1-24 are the hours from midnight one day through midnight the next
#   day.
#
# Observations:
#
# - At 13:53, HOEP report will have data with "Hour" column from 1 to 13.
#   Output and Capability report will have data with "Hour" column from 1 to
#   13. Intertie Flow report will have data with "Hour" column from 1 to 13
#   *and* Interval column from 1 to 12 for all of these hours, including the
#   13th hour.
# - At 14:18, HOEP report will go up to 14, Output report will go up to 14, but
#   update for Intertie report is not yet updated.
# - At 14:31, Intertie report is updated with Hour 14 which has Intervals 1 to
#   12.
#
# In the script, the Intertie report is shifted 1 hour and 5 minutes back, so
# that it lines up with the production and price data availability.

# Map IESO's exchange names to ours.
EXCHANGES = {
    "MANITOBA SK": "CA-MB->CA-ON",
    "MANITOBA": "CA-MB->CA-ON",
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
EXCHANGE_URL = "http://reports.ieso.ca/public/IntertieScheduleFlow/PUB_IntertieScheduleFlow_{YYYYMMDD}.xml"
# Map IESO's production modes to ours.
MODES = {
    "BIOFUEL": "biomass",
    "GAS": "gas",
    "HYDRO": "hydro",
    "NUCLEAR": "nuclear",
    "SOLAR": "solar",
    "WIND": "wind",
}
NAMESPACE = "{http://www.theIMO.com/schema}"
PRICE_URL = (
    "http://reports.ieso.ca/public/DispUnconsHOEP/PUB_DispUnconsHOEP_{YYYYMMDD}.xml"
)
PRODUCTION_URL = "http://reports.ieso.ca/public/GenOutputCapability/PUB_GenOutputCapability_{YYYYMMDD}.xml"
SOURCE = "ieso.ca"
# IESO says "Eastern Standard Time is used year round." This means daylight
# savings is not used (that is called "Eastern Daylight Time"), and we need to
# use UTC-5 rather than 'Canada/Eastern'.
TIMEZONE = timezone(timedelta(hours=-5), name="UTC-5")
ZONE_KEY = ZoneKey("CA-ON")


def _fetch_xml(
    logger: Logger,
    session: Session | None,
    target_datetime: datetime | None,
    url_template: str,
) -> tuple[date, ElementTree.Element | None]:
    date_ = (target_datetime or datetime.now(TIMEZONE)).astimezone(TIMEZONE).date()

    session = session or Session()
    url = url_template.format(YYYYMMDD=date_.strftime("%Y%m%d"))
    response = session.get(url)

    if not response.ok:
        # Historical data is generally available for 3 months; requesting
        # anything older returns an HTTP 404 error.
        logger.info(f"GET request to {url} failed")
        return date_, None

    return date_, ElementTree.fromstring(response.text)


def _parse_hour(element: ElementTree.Element) -> int:
    # Decrement the reported hour to convert from the hour-ending ([1, 24])
    # convention used by the source to our hour-starting ([0, 23]) convention.
    return int(element.findtext(NAMESPACE + "Hour")) - 1


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given region."""

    if zone_key != ZONE_KEY:
        raise NotImplementedError(f"unimplemented zone '{zone_key}'")

    date_, xml = _fetch_xml(logger, session, target_datetime, PRODUCTION_URL)

    if xml is None:
        return []

    # Collect the source data into a dictionary keying ProductionMix objects by
    # the time of day at which they occurred.
    mixes: defaultdict[time, ProductionMix] = defaultdict(ProductionMix)
    for generator in xml.iter(NAMESPACE + "Generator"):
        try:
            mode = MODES[generator.findtext(NAMESPACE + "FuelType")]
        except KeyError as error:
            logger.warning(error)
            continue
        for output in generator.iter(NAMESPACE + "Output"):
            try:
                hour = _parse_hour(output)
            except (TypeError, ValueError) as error:
                logger.warning(error)
                continue
            # The "EnergyMW" element will occasionally be absent from the XML
            # for a given plant at a given hour. In the browser, this is
            # displayed as an "N/A" entry in the table.
            generation = output.findtext(NAMESPACE + "EnergyMW")
            mixes[time(hour=hour)].add_value(
                mode, None if generation is None else float(generation)
            )

    production_breakdowns = ProductionBreakdownList(logger)
    for time_, mix in mixes.items():
        production_breakdowns.append(
            datetime=datetime.combine(date_, time_, tzinfo=TIMEZONE),
            production=mix,
            source=SOURCE,
            zoneKey=ZONE_KEY,
        )

    return production_breakdowns.to_list()


def fetch_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power price per MWh of a given region."""

    if zone_key != ZONE_KEY:
        raise NotImplementedError(f"unimplemented zone '{zone_key}'")

    date_, xml = _fetch_xml(logger, session, target_datetime, PRICE_URL)

    if not xml:
        return []

    # "HOEP" stands for "Hourly Ontario Energy Price". There also exists a
    # 5-minute price, but its archives only go back roughly 4 days (see "5
    # Minute Market Clearing Price" at http://www.ieso.ca/power-data ).
    prices = PriceList(logger)
    for hoep in xml.iter(NAMESPACE + "HOEP"):
        try:
            hour = _parse_hour(hoep)
        except (TypeError, ValueError) as error:
            logger.warning(error)
            continue
        price = hoep.findtext(NAMESPACE + "Price")
        prices.append(
            currency="CAD",
            datetime=datetime.combine(date_, time(hour=hour), tzinfo=TIMEZONE),
            price=None if price is None else float(price),
            source=SOURCE,
            zoneKey=zone_key,
        )

    return prices.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two regions."""

    sorted_zone_keys = ZoneKey("->".join(sorted((zone_key1, zone_key2))))

    if sorted_zone_keys not in EXCHANGES.values():
        raise NotImplementedError(f"unimplemented exchange '{sorted_zone_keys}'")

    date_, xml = _fetch_xml(logger, session, target_datetime, EXCHANGE_URL)

    if not xml:
        return []

    # Collect the source data into a dictionary keying exchange flows by the
    # time of day at which they occurred for the exchange of interest.
    flows: defaultdict[time, float] = defaultdict(float)
    for intertie in xml.iter(NAMESPACE + "IntertieZone"):
        zone_name = intertie.findtext(NAMESPACE + "IntertieZoneName")
        if zone_name not in EXCHANGES:
            logger.warning(f"unrecognized intertie '{zone_name}', please implement!")
            continue
        if EXCHANGES[zone_name] != sorted_zone_keys:
            # Ignore exchanges that we aren't interested in.
            continue
        for actual in intertie.iter(NAMESPACE + "Actual"):
            try:
                flow = float(actual.findtext(NAMESPACE + "Flow"))
                hour = _parse_hour(actual)
                # The source reports flows in twelve five-minute intervals
                # using an interval-ending convention (i.e., [1, 12]). Subtract
                # one from the interval and multiply the result by five to
                # convert to a minute-starting convention (0, 5, ..., 50, 55).
                minute = 5 * (int(actual.findtext(NAMESPACE + "Interval")) - 1)
            except (TypeError, ValueError) as error:
                logger.warning(error)
                continue
            # In the source data, flows out of Ontario (i.e., exports) are
            # positive. For us, positive flow follows the direction of the
            # arrow in sorted_zone_keys, so change the sign of the flow if
            # necessary.
            if not sorted_zone_keys.startswith("CA-ON->"):
                flow *= -1
            flows[time(hour=hour, minute=minute)] += flow

    exchanges = ExchangeList(logger)
    for time_, flow in flows.items():
        exchanges.append(
            datetime=datetime.combine(date_, time_, tzinfo=TIMEZONE),
            netFlow=flow,
            source=SOURCE,
            zoneKey=sorted_zone_keys,
        )

    return exchanges.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    now = datetime.now(timezone.utc)
    two_months_ago = now - timedelta(days=60)
    two_years_ago = now - timedelta(days=2 * 365)

    print("fetch_production() ->")
    print(fetch_production(), end="\n\n")

    print("data should be for " + now.astimezone(TIMEZONE).strftime("%Y-%m-%d"))
    print('fetch_production("CA-ON", target_datetime=now) ->')
    print(fetch_production(ZoneKey("CA-ON"), target_datetime=now), end="\n\n")

    print("we expect results for ~2 months ago")
    print("fetch_production(target_datetime=two_months_ago) ->")
    print(fetch_production(target_datetime=two_months_ago), end="\n\n")

    print("there are likely no results for ~2 years ago")
    print("fetch_production(target_datetime=two_years_ago) ->")
    print(fetch_production(target_datetime=two_years_ago), end="\n\n")

    print("fetch_price() ->")
    print(fetch_price(), end="\n\n")

    print("data should be for " + now.astimezone(TIMEZONE).strftime("%Y-%m-%d"))
    print("fetch_price(target_datetime=now) ->")
    print(fetch_price(target_datetime=now), end="\n\n")

    print("we expect results for ~2 months ago")
    print("fetch_price(target_datetime=two_months_ago) ->")
    print(fetch_price(target_datetime=two_months_ago), end="\n\n")

    print("there are likely no results for ~2 years ago")
    print("fetch_price(target_datetime=two_years_ago) ->")
    print(fetch_price(target_datetime=two_years_ago), end="\n\n")

    print('fetch_exchange("CA-ON", "US-NY-NYIS") ->')
    print(fetch_exchange(ZoneKey("CA-ON"), ZoneKey("US-NY-NYIS")), end="\n\n")

    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now) ->')
    print(
        fetch_exchange(ZoneKey("CA-ON"), ZoneKey("CA-QC"), target_datetime=now),
        end="\n\n",
    )

    print("Ontario-to-Manitoba must be opposite sign from reported IESO values")
    print('fetch_exchange("CA-ON", "CA-MB", target_datetime=now) ->')
    print(
        fetch_exchange(ZoneKey("CA-ON"), ZoneKey("CA-MB"), target_datetime=now),
        end="\n\n",
    )

    print("data should be for " + now.astimezone(TIMEZONE).strftime("%Y-%m-%d"))
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now) ->')
    print(
        fetch_exchange(ZoneKey("CA-ON"), ZoneKey("CA-QC"), target_datetime=now),
        end="\n\n",
    )

    print("we expect results for ~2 months ago")
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=two_months_ago) ->')
    print(
        fetch_exchange(
            ZoneKey("CA-ON"), ZoneKey("CA-QC"), target_datetime=two_months_ago
        ),
        end="\n\n",
    )

    print("there are likely no results for ~2 years ago")
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=two_years_ago) ->')
    print(
        fetch_exchange(
            ZoneKey("CA-ON"), ZoneKey("CA-QC"), target_datetime=two_years_ago
        ),
        end="\n\n",
    )

    print("requesting an exchange with Nova Scotia should raise exception")
    print('fetch_exchange("CA-ON", "CA-NS")) ->')
    try:
        fetch_exchange(ZoneKey("CA-ON"), ZoneKey("CA-NS"))
    except NotImplementedError:
        print("Task failed successfully")
