from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENTSOE
from parsers.lib.config import refetch_frequency


def get_solar_capacity_at(date: datetime) -> float:
    # Prepare historical records
    # Source https://www.uvek-gis.admin.ch/BFE/storymaps/EE_Elektrizitaetsproduktionsanlagen/?lang=en
    historical_capacities = pd.DataFrame.from_records(
        [
            ("2015-01-01", 1393.0),
            ("2016-01-01", 1646.0),
            ("2017-01-01", 1859.0),
            ("2018-01-01", 2090.0),
            ("2019-01-01", 2375.0),
            ("2020-01-01", 2795.0),
            ("2021-01-01", 3314.0),
            ("2022-01-01", 3904.0),
        ],
        columns=["datetime", "capacity.solar"],
    ).set_index("datetime")
    historical_capacities.index = pd.DatetimeIndex(
        historical_capacities.index, tz="UTC"
    )

    year = date.year
    if year < 2015:
        return historical_capacities.loc["2015-01-01", "capacity.solar"]
    else:
        mask = historical_capacities.index <= date
        return historical_capacities[mask].iloc[-1].loc["capacity.solar"]


def fetch_swiss_exchanges(session, target_datetime, logger):
    """Returns the total exchanges of Switzerland with its neighboring countries."""
    swiss_transmissions = {}
    for exchange_key in ["AT", "DE", "IT", "FR"]:
        exchanges = ENTSOE.fetch_exchange(
            zone_key1=ZoneKey("CH"),
            zone_key2=ZoneKey(exchange_key),
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
        if not exchanges:
            continue

        for exchange in exchanges:
            dt = exchange["datetime"]
            if dt not in swiss_transmissions:
                swiss_transmissions[dt] = exchange["netFlow"]
            else:
                swiss_transmissions[dt] += exchange["netFlow"]

    return swiss_transmissions


def fetch_swiss_consumption(
    session: Session, target_datetime: datetime, logger: Logger
):
    """Returns the total consumption of Switzerland."""
    consumptions = ENTSOE.fetch_consumption(
        zone_key=ZoneKey("CH"),
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    return {c["datetime"]: c["consumption"] for c in consumptions}


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("CH"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """
    Returns the total production by type for Switzerland.
    Currently, the majority of the run-of-river production is missing.
    The difference between the sum of all production types and the total production is allocated as 'unknown'.
    The total production is calculated as sum of the consumption, storage and net imports.
    """
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    r = session or Session()

    exchanges = fetch_swiss_exchanges(r, target_datetime, logger)
    consumptions = fetch_swiss_consumption(r, target_datetime, logger)
    productions = ENTSOE.fetch_production(
        zone_key=zone_key, session=r, target_datetime=target_datetime, logger=logger
    )

    if not productions:
        return

    for p in productions:
        dt = p["datetime"]
        if dt not in exchanges or dt not in consumptions:
            continue
        known_production = sum([x or 0 for x in p["production"].values()])

        storage = sum([x or 0 for x in p["storage"].values()])
        total_production = consumptions[dt] + storage + exchanges[dt]
        unknown_production = total_production - known_production
        p["production"]["unknown"] = unknown_production if unknown_production > 0 else 0

    for p in productions:
        p["capacity"] = {
            "solar": get_solar_capacity_at(p["datetime"]),
        }

    return productions


if __name__ == "__main__":
    print(fetch_production())
