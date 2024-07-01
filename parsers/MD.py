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
from electricitymap.contrib.lib.models.events import EventSourceType, ProductionMix
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


# Moldoelectrica electricity tariffs as defined by government-agency decisions.
_MOLDOELECTRICA_NEW_POWER_PRICE_IN_MDL_PER_MW = {
    # https://www.legis.md/cautare/getResults?doc_id=78826&lang=ro
    datetime(2000, 4, 1, tzinfo=timezone.utc): 18.8,
    # https://www.legis.md/cautare/getResults?doc_id=103953&lang=ro
    datetime(2001, 10, 1, tzinfo=timezone.utc): 28.0,
    # https://www.legis.md/cautare/getResults?doc_id=40249&lang=ro
    datetime(2002, 9, 1, tzinfo=timezone.utc): 35.2,
    # https://www.legis.md/cautare/getResults?doc_id=42701&lang=ro
    datetime(2005, 9, 1, tzinfo=timezone.utc): 39.3,
    # https://www.legis.md/cautare/getResults?doc_id=10948&lang=ro
    datetime(2007, 8, 3, tzinfo=timezone.utc): 51.8,
    # https://www.legis.md/cautare/getResults?doc_id=40130&lang=ro
    datetime(2010, 1, 19, tzinfo=timezone.utc): 63.2,
    # https://www.legis.md/cautare/getResults?doc_id=40589&lang=ro
    datetime(2012, 5, 11, tzinfo=timezone.utc): 80.2,
    # https://www.legis.md/cautare/getResults?doc_id=84436&lang=ro
    datetime(2015, 7, 31, tzinfo=timezone.utc): 145.0,
    # https://www.legis.md/cautare/getResults?doc_id=134854&lang=ro
    datetime(2023, 12, 31, tzinfo=timezone.utc): 201.0,
    # https://www.legis.md/cautare/getResults?doc_id=142391&lang=ro
    datetime(2024, 3, 21, tzinfo=timezone.utc): 185.0,
    # TODO(amv213): update as new tariffs get rolled out...
}


class ArchiveDatapoint(NamedTuple):
    """Datapoint returned by the archive_url with ordered fetchable fields."""

    datetime: datetime
    consumption: float | None
    planned_consumption: float | None
    production: float | None
    planned_production: float | None
    tpp: float | None  # production from thermal power plants
    hpp: float | None  # production from hydro power plants
    res: float | None  # production from renewable energy sources
    exchange_UA_to_MD: float | None
    planned_exchange_UA_to_MD: float | None
    exchange_RO_to_MD: float | None
    planned_exchange_RO_to_MD: float | None


def _get_archive_data(
    target_datetime: datetime | None,
    session: Session | None,
    num_backlog_days: int = 0,
) -> list[ArchiveDatapoint]:
    """Returns archive data in 15 mn buckets for the UTC day of interest and (optionally) previous ones."""

    target_utc_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    target_utc_day = datetime.combine(target_utc_datetime, time(), tzinfo=timezone.utc)
    target_utc_timestamp_from, target_utc_timestamp_to = (
        target_utc_day - timedelta(days=num_backlog_days),
        target_utc_day + timedelta(days=1) - timedelta(seconds=1),
    )

    # the API works in local (TZ) timestamps
    date1 = target_utc_timestamp_from.astimezone(TZ).strftime("%d.%m.%Y")
    date2 = target_utc_timestamp_to.astimezone(TZ).strftime("%d.%m.%Y")
    archive_url = f"{ARCHIVE_BASE_URL}&date1={date1}&date2={date2}"

    s = session or Session()
    response = s.get(archive_url)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching data error code: {response.status_code}: {response.text}",
        )

    data = response.json()

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

            # keep in mind that some values might be null
            datapoint = ArchiveDatapoint(
                dt_utc, *(float(x) if x is not None else x for x in entry[1:])
            )
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

    This will be a static power price for Moldoelectrica electricity as defined by government-agency decision.

    References:
        https://www.anre.md/energie-electrica-3-290
        https://moldelectrica.md/ro/activity/tariff
    """
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    # find price band for given target datetime
    prices = iter(_MOLDOELECTRICA_NEW_POWER_PRICE_IN_MDL_PER_MW.items())
    _, price = next(
        prices
    )  # assume base price for times before we could find references
    for dt, new_price in prices:
        if target_datetime < dt:
            break
        price = new_price

    price_list = PriceList(logger=logger)
    price_list.append(
        zoneKey=zone_key,
        datetime=target_datetime.replace(minute=0, second=0, microsecond=0),
        source=SOURCE,
        price=price,
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
    archive_data = _get_archive_data(
        target_datetime, session=session, num_backlog_days=1
    )

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

    archive_data = _get_archive_data(
        target_datetime, session=session, num_backlog_days=1
    )

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


def _fetch_exchange(
    event_type: EventSourceType,
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None,
    target_datetime: datetime | None,
    logger: Logger,
    num_backlog_days: int,
) -> list[dict]:
    """Requests measured or forecasted power exchange (in MW) between two zones."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if ZONE_KEY not in {zone_key1, zone_key2}:
        raise ParserException(
            PARSER,
            f"This parser can only parse exchanges to / from {ZONE_KEY}.",
            sorted_zone_keys,
        )

    archive_data = _get_archive_data(
        target_datetime,
        session=session,
        num_backlog_days=num_backlog_days,
    )

    use_actual = event_type == EventSourceType.measured

    exchange_list = ExchangeList(logger=logger)
    for entry in archive_data:
        netflow = None

        if sorted_zone_keys == ZoneKey("MD->UA"):
            netflow = (
                entry.exchange_UA_to_MD
                if use_actual
                else entry.planned_exchange_UA_to_MD
            )

        elif sorted_zone_keys == ZoneKey("MD->RO"):
            netflow = (
                entry.exchange_RO_to_MD
                if use_actual
                else entry.planned_exchange_RO_to_MD
            )
        else:
            raise NotImplementedError(f"{sorted_zone_keys} pair is not implemented")

        if netflow != 0 and netflow is not None:
            netflow *= -1

        exchange_list.append(
            zoneKey=sorted_zone_keys,
            datetime=entry.datetime,
            netFlow=netflow,
            source=SOURCE,
            sourceType=event_type,
        )

    return exchange_list.to_list()


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the known power exchange (in MW) between two zones."""
    return _fetch_exchange(
        event_type=EventSourceType.measured,
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        num_backlog_days=1,
    )


@refetch_frequency(timedelta(days=2))
def fetch_exchange_forecast(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the forecasted power exchange (in MW) between two zones."""
    return _fetch_exchange(
        event_type=EventSourceType.forecasted,
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        num_backlog_days=1,
    )


if __name__ == "__main__":
    # Main method, never used by the Electricity Map backend, but handy for testing.

    for target_datetime in (None, datetime.fromisoformat("2021-07-25T15:00+00:00")):
        print(f"fetch_price({target_datetime=}) ->")
        print(fetch_price(target_datetime=target_datetime))

        print(f"fetch_consumption({target_datetime=}) ->")
        print(fetch_consumption(target_datetime=target_datetime))

        print(f"fetch_production({target_datetime=}) ->")
        print(fetch_production(target_datetime=target_datetime))

        for neighbour in ["RO", "UA"]:
            print(f"fetch_exchange({ZONE_KEY}, {neighbour}, {target_datetime=}) ->")
            print(
                fetch_exchange(
                    ZONE_KEY, ZoneKey(neighbour), target_datetime=target_datetime
                )
            )

            print(
                f"fetch_exchange_forecast({ZONE_KEY}, {neighbour}, {target_datetime=}) ->"
            )
            print(
                fetch_exchange_forecast(
                    ZONE_KEY, ZoneKey(neighbour), target_datetime=target_datetime
                )
            )
