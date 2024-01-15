#!/usr/bin/env python3
import datetime
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
TIMEZONE = datetime.timezone(datetime.timedelta(hours=-5), name="UTC-5")
ZONE_KEY = ZoneKey("CA-ON")


def _fetch_xml(
    logger: Logger,
    session: Session | None,
    target_datetime: datetime.datetime | None,
    template: str,
) -> tuple[datetime.date, ElementTree.Element | None]:
    date = (
        (target_datetime or datetime.datetime.now(TIMEZONE)).astimezone(TIMEZONE).date()
    )

    session = session or Session()
    url = template.format(YYYYMMDD=date.strftime("%Y%m%d"))
    response = session.get(url)

    if not response.ok:
        # Historical data is generally available for 3 months; requesting
        # anything older returns an HTTP 404 error.
        logger.info(f"GET request to {url} failed")
        return date, None

    return date, ElementTree.fromstring(response.text)


def _parse_hour(element):
    # Decrement the reported hour to convert from the hour-ending ([1, 24])
    # convention used by the source to our hour-starting ([0, 23]) convention.
    return int(element.findtext(NAMESPACE + "Hour")) - 1


def fetch_production(
    zone_key: str = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime.datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given region."""

    if zone_key != ZONE_KEY:
        raise NotImplementedError(f"unimplemented zone '{zone_key}'")

    date, xml = _fetch_xml(logger, session, target_datetime, PRODUCTION_URL)

    if xml is None:
        return []

    # Collect the source data into a dictionary keying ProductionMix objects by
    # the time of day at which they occurred.
    mixes = {}
    for generator in xml.iter(NAMESPACE + "Generator"):
        mode = MODES[generator.findtext(NAMESPACE + "FuelType")]
        for output in generator.iter(NAMESPACE + "Output"):
            generation = output.findtext(NAMESPACE + "EnergyMW")
            mixes.setdefault(
                datetime.time(hour=_parse_hour(output)), ProductionMix()
            ).add_value(
                mode,
                # Sometimes the XML data has no EnergyMW tag for a given plant
                # at a given hour. The report XSL formats this as "N/A"; we
                # return 0.
                # TODO: Is XSL supposed to be XML? I've never seen an N/A in
                # the response, and if one appeared we'd have to test for
                # generation == "N/A", not generation is None. If the EnergyMW
                # element is just absent, then the generation is None test
                # makes sense.
                # TODO: Should we set this to None instead of 0?
                0 if generation is None else float(generation),
            )

    production_breakdowns = ProductionBreakdownList(logger)
    for time, mix in mixes.items():
        production_breakdowns.append(
            datetime=datetime.datetime.combine(date, time, tzinfo=TIMEZONE),
            production=mix,
            source=SOURCE,
            zoneKey=ZONE_KEY,
        )

    return production_breakdowns.to_list()


def fetch_price(
    zone_key: str = ZoneKey("CA-ON"),
    session: Session | None = None,
    target_datetime: datetime.datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power price per MWh of a given region."""

    if zone_key != ZONE_KEY:
        raise NotImplementedError(f"unimplemented zone '{zone_key}'")

    date, xml = _fetch_xml(logger, session, target_datetime, PRICE_URL)

    if not xml:
        return []

    # "HOEP" stands for "Hourly Ontario Energy Price". There also exists a
    # 5-minute price, but its archives only go back roughly 4 days (see "5
    # Minute Market Clearing Price" at http://www.ieso.ca/power-data ).
    prices = PriceList(logger)
    for hoep in xml.iter(NAMESPACE + "HOEP"):
        prices.append(
            currency="CAD",
            datetime=datetime.datetime.combine(
                date, datetime.time(hour=_parse_hour(hoep)), tzinfo=TIMEZONE
            ),
            price=float(hoep.findtext(NAMESPACE + "Price")),
            source=SOURCE,
            zoneKey=zone_key,
        )

    return prices.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime.datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two regions."""

    sorted_zone_keys = "->".join(sorted((zone_key1, zone_key2)))

    if sorted_zone_keys not in EXCHANGES.values():
        raise NotImplementedError(f"unimplemented exchange '{sorted_zone_keys}'")

    date, xml = _fetch_xml(logger, session, target_datetime, EXCHANGE_URL)

    if not xml:
        return []

    # Collect the source data into a dictionary keying exchange flows by the
    # time of day at which they occurred for the exchange of interest.
    flows = {}
    for intertie in xml.iter(NAMESPACE + "IntertieZone"):
        zone_name = intertie.findtext(NAMESPACE + "IntertieZoneName")
        if zone_name not in EXCHANGES:
            logger.warning(f"unrecognized intertie '{zone_name}', please implement!")
            continue
        if EXCHANGES[zone_name] != sorted_zone_keys:
            # Ignore exchanges that we aren't interested in.
            continue
        for actual in intertie.iter(NAMESPACE + "Actual"):
            # The IESO day starts with Hour 1, Interval 1. At 11:37, we might
            # have data for up to Hour 11, Interval 12. This means it is
            # necessary to subtract 1 from the values (otherwise we would have
            # data for 12:00 already at 11:37).
            time = datetime.time(
                hour=_parse_hour(actual),
                minute=5 * (int(actual.findtext(NAMESPACE + "Interval")) - 1),
            )
            # In the source data, flows out of Ontario (i.e., exports) are
            # positive. For us, positive flow follows the direction of the
            # arrow in sorted_zone_keys, so change the sign of the flow if
            # necessary.
            flow = float(actual.findtext(NAMESPACE + "Flow"))
            if not sorted_zone_keys.startswith("CA-ON->"):
                flow *= -1
            flows[time] = flows.get(time, 0) + flow

    exchanges = ExchangeList(logger)
    for time, flow in flows.items():
        exchanges.append(
            datetime=datetime.datetime.combine(date, time, tzinfo=TIMEZONE),
            netFlow=flow,
            source=SOURCE,
            zoneKey=sorted_zone_keys,
        )

    return exchanges.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    now = datetime.datetime.now(datetime.timezone.utc)
    two_months_ago = now - datetime.timedelta(days=60)
    two_years_ago = now - datetime.timedelta(days=2 * 365)

    print("fetch_production() ->")
    print(fetch_production(), end="\n\n")

    print("data should be for " + now.astimezone(TIMEZONE).strftime("%Y-%m-%d"))
    print('fetch_production("CA-ON", target_datetime=now) ->')
    print(fetch_production("CA-ON", target_datetime=now), end="\n\n")

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
    print(fetch_exchange("CA-ON", "US-NY-NYIS"), end="\n\n")

    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now), end="\n\n")

    print("Ontario-to-Manitoba must be opposite sign from reported IESO values")
    print('fetch_exchange("CA-ON", "CA-MB", target_datetime=now) ->')
    print(fetch_exchange("CA-ON", "CA-MB", target_datetime=now), end="\n\n")

    print("data should be for " + now.astimezone(TIMEZONE).strftime("%Y-%m-%d"))
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now), end="\n\n")

    print("we expect results for ~2 months ago")
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=two_months_ago) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=two_months_ago), end="\n\n")

    print("there are likely no results for ~2 years ago")
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=two_years_ago) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=two_years_ago), end="\n\n")

    print("requesting an exchange with Nova Scotia should raise exception")
    print('fetch_exchange("CA-ON", "CA-NS")) ->')
    try:
        fetch_exchange("CA-ON", "CA-NS")
    except NotImplementedError:
        print("Success")
