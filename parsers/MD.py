"""Parser for Moldova."""

# Further information on the equipment used at CERS Moldovenească can be found at:
# http://moldgres.com/o-predpriyatii/equipment
# Further information on the fuel-mix used at CERS Moldovenească can be found at:
# http://moldgres.com/search/%D0%9F%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B5%20%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B8
# (by searching for 'Производственные показатели' aka. 'Performance Indicators')
# Data for the fuel-mix at CERS Moldovenească for the year 2020 can be found at:
# http://moldgres.com/wp-content/uploads/2021/02/proizvodstvennye-pokazateli-zao-moldavskaja-gres-za-2020-god.pdf

# Annual reports from moldelectrica can be found at:
# https://moldelectrica.md/ro/network/annual_report

from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from operator import attrgetter
from typing import NamedTuple
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

PARSER = "MD.py"
TZ = ZoneInfo("Europe/Chisinau")
ZONE_KEY = ZoneKey("MD")

# Supports the following formats:
# - type=csv for zip-data with semicolon-separated-values
# - type=array for a 2D json-array containing an array for each datapoint
# - type=html for a HTML-table (default when no type is given)
ARCHIVE_BASE_URL = "https://moldelectrica.md/utils/archive2.php?id=table&type=array"
SOURCE = "moldelectrica.md"


class ArchiveDatapoint(NamedTuple):
    """Datapoint returned by the archive_url with ordered fetchable fields."""

    datetime: datetime
    consumption: float
    planned_consumption: float
    production: float
    planned_production: float
    tpp: float  # production from thermal power plants
    hpp: float  # production from hydro power plants
    res: float  # production from renewable energy sources
    exchange_UA_to_MD: float
    planned_exchange_UA_to_MD: float
    exchange_RO_to_MD: float
    planned_exchange_RO_to_MD: float


def get_archive_data(
    target_datetime: datetime | None,
    session: Session | None,
    backlog_days: int = 0,
) -> list[ArchiveDatapoint]:
    """Returns archive data in 15 mn buckets for the UTC day of interest and (optionally) previous ones."""

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
    archive_url = f"{ARCHIVE_BASE_URL}&date1={date1}&date2={date2}"

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
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power price of a given zone.

    This will be a static power price of 0.145 MDL per kWh. It is defined by a government-agency decision,
    which is still in effect at the time of writing this (July 2021).

    References:
        https://moldelectrica.md/ro/activity/tariff
        http://lex.justice.md/viewdoc.php?action=view&view=doc&id=360109&lang=1
    """
    if target_datetime:
        raise ParserException(
            PARSER,
            "This parser is not yet able to parse past dates",
            zone_key,
        )

    price_list = PriceList(logger=logger)
    price_list.append(
        zoneKey=zone_key,
        datetime=datetime.now(timezone.utc),
        source=SOURCE,
        price=145.0,
        currency="MDL",
    )
    return price_list.to_list()


@refetch_frequency(timedelta(days=2))
def fetch_consumption(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power consumption (in MW) of a given zone."""
    archive_data = get_archive_data(target_datetime, session=session, backlog_days=1)

    consumption_list = TotalConsumptionList(logger=logger)

    for archive_datapoint in archive_data:
        consumption_list.append(
            zoneKey=zone_key,
            datetime=archive_datapoint.datetime,
            source=SOURCE,
            consumption=archive_datapoint.consumption,
        )
    return consumption_list.to_list()


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the production mix (in MW) of a given zone."""

    archive_data = get_archive_data(target_datetime, session=session, backlog_days=1)

    production_list = ProductionBreakdownList(logger=logger)

    for archive_datapoint in archive_data:
        production_mix = ProductionMix()
        production_mix.add_value("gas", archive_datapoint.tpp)
        production_mix.add_value("hydro", archive_datapoint.hpp)
        # Renewables (solar + biogas + wind) make up a small part of the energy produced.
        # The exact mix of renewable energy sources is unknown,
        # so everything is attributed to biomass.
        production_mix.add_value("biomass", archive_datapoint.res)

        production_list.append(
            zoneKey=zone_key,
            datetime=archive_datapoint.datetime,
            source=SOURCE,
            production=production_mix,
        )

    return production_list.to_list()


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if ZONE_KEY not in {zone_key1, zone_key2}:
        raise ParserException(
            PARSER,
            f"This parser can only parse exchanges to / from {ZONE_KEY}.",
            sorted_zone_keys,
        )

    archive_data = get_archive_data(target_datetime, session=session, backlog_days=1)

    exchange_list = ExchangeList(logger=logger)

    for entry in archive_data:
        if sorted_zone_keys == ZoneKey("MD->UA"):
            netflow = -1 * entry.exchange_UA_to_MD
        elif sorted_zone_keys == ZoneKey("MD->RO"):
            netflow = -1 * entry.exchange_RO_to_MD
        else:
            raise NotImplementedError(f"{sorted_zone_keys} pair is not implemented")

        exchange_list.append(
            zoneKey=sorted_zone_keys,
            datetime=entry.datetime,
            netFlow=netflow,
            source=SOURCE,
        )

    return exchange_list.to_list()


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

        for neighbour in ["RO", "UA"]:
            print(f"fetch_exchange({ZONE_KEY}, {neighbour}) ->")
            print(
                fetch_exchange(
                    ZONE_KEY, ZoneKey(neighbour), target_datetime=target_datetime
                )
            )
