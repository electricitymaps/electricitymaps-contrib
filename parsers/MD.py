"""Parser for Moldova."""

from collections import namedtuple
from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from operator import attrgetter
from zoneinfo import ZoneInfo

from requests import Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

TZ = ZoneInfo("Europe/Chisinau")

# Supports the following formats:
# - type=csv for zip-data with semicolon-separated-values
# - type=array for a 2D json-array containing an array for each datapoint
# - type=html for a HTML-table (default when no type is given)
archive_base_url = "https://moldelectrica.md/utils/archive2.php?id=table&type=array"

# Fields that can be fetched from archive_url in order.
archive_fields = (
    "datetime",
    "consumption",
    "planned_consumption",
    "production",
    "planned_production",
    "tpp",  # production from thermal power plants
    "hpp",  # production from thermal power plants
    "res",  # production from renewable energy sources
    "exchange_UA_to_MD",
    "planned_exchange_UA_to_MD",
    "exchange_RO_to_MD",
    "planned_exchange_RO_to_MD",
)

# Datapoint in the archive-data.
ArchiveDatapoint = namedtuple("ArchiveDatapoint", archive_fields)

# Further information on the equipment used at CERS Moldovenească can be found at:
# http://moldgres.com/o-predpriyatii/equipment
# Further information on the fuel-mix used at CERS Moldovenească can be found at:
# http://moldgres.com/search/%D0%9F%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B5%20%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B8
# (by searching for 'Производственные показатели' aka. 'Performance Indicators')
# Data for the fuel-mix at CERS Moldovenească for the year 2020 can be found at:
# http://moldgres.com/wp-content/uploads/2021/02/proizvodstvennye-pokazateli-zao-moldavskaja-gres-za-2020-god.pdf

# Annual reports from moldelectrica can be found at:
# https://moldelectrica.md/ro/network/annual_report


def template_price_response(zone_key: str, datetime: datetime, price) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "currency": "MDL",
        "price": price,
        "source": "moldelectrica.md",
    }


def template_consumption_response(
    zone_key: str, datetime: datetime, consumption
) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "consumption": consumption,
        "source": "moldelectrica.md",
    }


def template_production_response(zone_key: str, datetime: datetime, production) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": production,
        "storage": {},
        "source": "moldelectrica.md",
    }


def template_exchange_response(
    sorted_zone_keys: str, datetime: datetime, netflow
) -> dict:
    return {
        "sortedZoneKeys": sorted_zone_keys,
        "datetime": datetime,
        "netFlow": netflow,
        "source": "moldelectrica.md",
    }


def get_archive_data(
    target_datetime: datetime | None,
    session: Session | None,
    backlog_days: int = 0,
) -> list[ArchiveDatapoint]:
    """Returns archive data in 15 mn buckets for the day of interest and (optionally) previous ones."""

    target_utc_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    target_utc_day = datetime.combine(target_utc_datetime, time(), tzinfo=timezone.utc)
    target_utc_timestamp_from, target_utc_timestamp_to = (
        target_utc_day - timedelta(days=backlog_days),
        target_utc_day + timedelta(days=1) - timedelta(seconds=1),
    )

    # the API works in local (TZ) timestamps
    date1 = target_utc_timestamp_from.astimezone(TZ).strftime("%d.%m.%Y")
    date2 = target_utc_timestamp_to.astimezone(TZ).strftime("%d.%m.%Y")
    archive_url = f"{archive_base_url}&date1={date1}&date2={date2}"

    s = session or Session()
    data_response = s.get(archive_url)
    data = data_response.json()

    try:
        archive_datapoints = []
        for entry in data:
            dt_utc = (
                datetime.strptime(entry[0], "%Y-%m-%d %H:%M")
                .replace(tzinfo=TZ)
                .astimezone(timezone.utc)
            )

            # filter out results outside of UTC target range
            # The API returns data for whole TZ days, so some data might be outside boundaries
            if dt_utc < target_utc_timestamp_from or dt_utc > target_utc_timestamp_to:
                continue

            datapoint = ArchiveDatapoint(dt_utc, *map(float, entry[1:]))
            archive_datapoints.append(datapoint)

        return sorted(archive_datapoints, key=attrgetter("datetime"))

    except Exception as e:
        raise ParserException(
            "MD.py",
            "Not able to parse received data. Check that the specifed URL returns correct data.",
        ) from e


def fetch_price(
    zone_key: str = "MD",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """
    Returns the static price of electricity (0.145 MDL per kWh) as specified here:
    https://moldelectrica.md/ro/activity/tariff
    It is defined by the following government-agency decision,
    which is still in effect at the time of writing this (July 2021):
    http://lex.justice.md/viewdoc.php?action=view&view=doc&id=360109&lang=1
    """
    if target_datetime:
        raise NotImplementedError(
            "This parser is not yet able to parse past dates for price"
        )

    dt = datetime.now(timezone.utc)
    return template_price_response(zone_key, dt, 145.0)


@refetch_frequency(timedelta(days=2))
def fetch_consumption(
    zone_key: str = "MD",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the consumption (in MW) of a given country."""
    archive_data = get_archive_data(target_datetime, session=session, backlog_days=1)

    datapoints = []
    for entry in archive_data:
        datapoint = template_consumption_response(
            zone_key, entry.datetime, entry.consumption
        )
        datapoints.append(datapoint)
    return datapoints


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: str = "MD",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the production mix (in MW) of a given country."""
    archive_data = get_archive_data(target_datetime, session=session, backlog_days=1)
    datapoints = []
    for entry in archive_data:
        production = {
            "solar": None,
            "wind": None,
            "biomass": 0.0,
            "nuclear": None,
            "gas": 0.0,
            "hydro": 0.0,
        }

        production["gas"] += entry.tpp
        production["hydro"] += entry.hpp
        # Renewables (solar + biogas + wind) make up a small part of the energy produced.
        # The exact mix of renewable enegry sources is unknown,
        # so everything is attributed to biomass.
        production["biomass"] += entry.res

        datapoint = template_production_response(zone_key, entry.datetime, production)
        datapoints.append(datapoint)
    return datapoints


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the last known power exchange (in MW) between two countries."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    archive_data = get_archive_data(target_datetime, session=session, backlog_days=1)

    datapoints = []
    for entry in archive_data:
        if sorted_zone_keys == "MD->UA":
            netflow = -1 * entry.exchange_UA_to_MD
        elif sorted_zone_keys == "MD->RO":
            netflow = -1 * entry.exchange_RO_to_MD
        else:
            raise NotImplementedError("This exchange pair is not implemented")

        datapoint = template_exchange_response(
            sorted_zone_keys, entry.datetime, netflow
        )
        datapoints.append(datapoint)
    return datapoints


if __name__ == "__main__":
    # Main method, never used by the Electricity Map backend, but handy for testing.

    print("fetch_price() ->")
    print(fetch_price())

    for target_datetime in (None, datetime.fromisoformat("2021-07-25T15:00+00:00")):
        print(f"For target_datetime {target_datetime}:")

        print("fetch_consumption() ->")
        print(fetch_consumption(target_datetime=target_datetime))

        print("fetch_production() ->")
        print(fetch_production(target_datetime=target_datetime))

        print("fetch_exchange(MD, UA) ->")
        print(fetch_exchange("MD", "UA", target_datetime=target_datetime))
        print("fetch_exchange(MD, RO) ->")
        print(fetch_exchange("MD", "RO", target_datetime=target_datetime))

        print("------------")
