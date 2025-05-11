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
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import EventSourceType, ProductionMix
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


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the demand forecast (in MW) of Canada Ontario zone for 7 days ahead hourly."""
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(TIMEZONE)

    # Dictionary to store extracted data
    consumption_list = TotalConsumptionList(logger)

    # Extract the file in adequacy folder until 7 days later.
    # They have forecast until 34 days, but depends at what time of the day the url is extracted, the 34th day might not be published yet
    end_date = target_datetime + timedelta(days=7)

    # Iterate on every available date
    current_date = target_datetime
    while current_date <= end_date:
        # Extract Adequacy report
        date_, xml = _fetch_xml(logger, session, current_date, ADEQUACY_URL)

        # Define the namespace (if applicable)
        NAMESPACE = "{http://www.ieso.ca/schema}"
        ns = {"ns0": "http://www.ieso.ca/schema"}

        forecast_date = xml.find(".//ns0:DeliveryDate", ns)

        for forecast_ontario_demand in xml.findall(".//ns0:ForecastOntDemand", ns):
            for demand in forecast_ontario_demand.findall(".//ns0:Demand", ns):
                delivery_hour = demand.findtext(NAMESPACE + "DeliveryHour")
                date_object = datetime.strptime(forecast_date.text, "%Y-%m-%d").replace(
                    tzinfo=TIMEZONE
                )
                date_object = date_object.replace(hour=int(delivery_hour) - 1)
                energy_mw = demand.findtext(NAMESPACE + "EnergyMW")

                # Update consumption list
                consumption_list.append(
                    zoneKey=zone_key,
                    datetime=date_object,
                    consumption=float(energy_mw) if energy_mw is not None else None,
                    source=SOURCE,
                    sourceType=EventSourceType.forecasted,
                )

        current_date += timedelta(days=1)  # Go to next day

    return consumption_list.to_list()


def read_adequacy_report(root, logger):
    """Helper function for fetch_wind_solar_forecasts() that reads Adequacy report for a given xml root"""
    NAMESPACE = "{http://www.ieso.ca/schema}"
    ns = {"ns0": "http://www.ieso.ca/schema"}

    # Dictionary to store extracted data
    production_list = ProductionBreakdownList(logger)
    forecast_date = root.find(".//ns0:DeliveryDate", ns)

    # Dictionary to store ProductionMix for each timestamp
    mixes: dict[datetime, ProductionMix] = {}

    # Iterate through InternalResource elements
    for resource in root.findall(".//ns0:InternalResource", ns):
        mode = resource.findtext(NAMESPACE + "FuelType")
        if mode == "Wind" or mode == "Solar":
            for c in resource.findall("ns0:Forecasts", ns):
                for value in c.findall("ns0:Forecast", ns):
                    date_object = datetime.strptime(
                        forecast_date.text, "%Y-%m-%d"
                    ).replace(tzinfo=TIMEZONE)
                    delivery_hour = value.findtext(NAMESPACE + "DeliveryHour")
                    date_object = date_object.replace(hour=int(delivery_hour) - 1)
                    timestamp = date_object
                    energy_mw = value.findtext(NAMESPACE + "EnergyMW")

                    # Create production mix
                    mix: defaultdict[datetime, ProductionMix] = defaultdict(
                        ProductionMix
                    )
                    mix[date_object].add_value(
                        mode.lower(),
                        None if energy_mw is None else float(energy_mw),
                        correct_negative_with_zero=True,
                    )

                    # Get or create ProductionMix for this timestamp
                    if timestamp not in mixes:
                        mixes[timestamp] = ProductionMix()

                    # Add wind/solar output to the existing ProductionMix
                    mixes[timestamp].add_value(
                        mode.lower(),
                        None if energy_mw is None else float(energy_mw),
                        correct_negative_with_zero=True,
                    )

                    # Check if this datetime already exists in the production_list
                    datetime_exists = any(
                        item["datetime"] == date_object for item in production_list
                    )

                    # Only append if the datetime doesn't exist yet
                    if not datetime_exists:
                        production_list.append(
                            zoneKey=ZONE_KEY,
                            datetime=date_object,
                            production=mix[date_object],
                            source=SOURCE,
                            sourceType=EventSourceType.forecasted,
                        )

    return production_list


def read_VGForecastSummary_report(root, logger):
    """Helper function for fetch_wind_solar_forecasts() that reads VGForecastsSummary report for a given XML root."""

    ns = {"ns0": "http://www.ieso.ca/schema"}
    production_list = ProductionBreakdownList(logger)

    # Dictionary to store ProductionMix for each timestamp
    mixes: dict[datetime, ProductionMix] = {}

    for org_data in root.findall(".//ns0:OrganizationData", ns):
        for fuel_data in org_data.findall(".//ns0:FuelData", ns):
            fuel_type = fuel_data.find("ns0:FuelType", ns).text.lower()

            for resource in fuel_data.findall(".//ns0:ResourceData", ns):
                zone = resource.find("ns0:ZoneName", ns)

                if zone.text == "OntarioTotal":
                    for energy_forecast in resource.findall(
                        ".//ns0:EnergyForecast", ns
                    ):
                        forecast_date = energy_forecast.find("ns0:ForecastDate", ns)
                        base_date = datetime.strptime(
                            forecast_date.text, "%Y-%m-%d"
                        ).replace(tzinfo=TIMEZONE)

                        for forecast_interval in energy_forecast.findall(
                            ".//ns0:ForecastInterval", ns
                        ):
                            forecast_hour_ending = forecast_interval.find(
                                "ns0:ForecastHour", ns
                            )
                            timestamp = base_date.replace(
                                hour=int(forecast_hour_ending.text) - 1
                            )

                            mw_output = forecast_interval.find("ns0:MWOutput", ns)
                            mw_value = (
                                None if mw_output is None else float(mw_output.text)
                            )

                            # Get or create ProductionMix for this timestamp
                            if timestamp not in mixes:
                                mixes[timestamp] = ProductionMix()

                            # Add wind/solar output to the existing ProductionMix
                            mixes[timestamp].add_value(
                                fuel_type,
                                mw_value,
                                correct_negative_with_zero=True,
                            )

    # Append all combined ProductionMix objects to production_list
    for timestamp, mix in mixes.items():
        production_list.append(
            zoneKey=ZONE_KEY,
            datetime=timestamp,
            production=mix,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return production_list


ADEQUACY_URL = (
    "https://reports-public.ieso.ca/public/Adequacy2/PUB_Adequacy2_{YYYYMMDD}.xml"
)
VG_FORECAST_SUMMARY = "https://reports-public.ieso.ca/public/VGForecastSummary/PUB_VGForecastSummary_{YYYYMMDD}.xml"


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the forecasts for wind and solar (in MW) of Canada Ontario zone for 7 days ahead."""
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(TIMEZONE)

    # Extract the file in adequacy folder until 7 days later.
    # They have forecast until 34 days, but depends at what time of the day the url is extracted, the 34th day might not be published yet
    end_date = target_datetime + timedelta(days=7)

    # Direct iteration method
    production_list = ProductionBreakdownList(logger)
    current_date = target_datetime
    while current_date <= end_date:
        # First try to get the VG Forecast Summary report
        date_, xml = _fetch_xml(logger, session, current_date, VG_FORECAST_SUMMARY)

        # Check if the data is available before trying to read it
        if xml is not None:
            production_list_1 = read_VGForecastSummary_report(xml, logger)
        else:
            # When VG Forecast is not available, use Adequacy report instead
            date_, xml = _fetch_xml(logger, session, current_date, ADEQUACY_URL)
            production_list_1 = read_adequacy_report(xml, logger)

        production_list = ProductionBreakdownList.merge_production_breakdowns(
            [production_list, production_list_1], logger
        )

        current_date += timedelta(days=1)
    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    """
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
    """

    # print("Requesting fetch_wind_solar_forecasts")
    # pprint(fetch_wind_solar_forecasts())

    print("Requesting fetch_consumption_forecast")
    pprint(fetch_consumption_forecast())
