#!/usr/bin/env python3


from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Union

import arrow
import pandas as pd
from requests import Session

from parsers.lib.config import refetch_frequency

from . import ENTSOE


def get_solar_capacity_at(date: datetime) -> float:
    # Prepare historical records
    # Source https://www.uvek-gis.admin.ch/BFE/storymaps/EE_Elektrizitaetsproduktionsanlagen/?lang=en
    historical_capacities = pd.DataFrame.from_records(
        [
            ("2015-01-01", 1385),
            ("2016-01-01", 1632),
            ("2017-01-01", 1844),
            ("2018-01-01", 2070),
            ("2019-01-01", 2346),
            ("2020-01-01", 2749),
            ("2021-01-01", 3129),
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
            zone_key1="CH",
            zone_key2=exchange_key,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
        if not exchanges:
            continue

        for exchange in exchanges:
            datetime = exchange["datetime"]
            if datetime not in swiss_transmissions:
                swiss_transmissions[datetime] = exchange["netFlow"]
            else:
                swiss_transmissions[datetime] += exchange["netFlow"]

    return swiss_transmissions


def fetch_swiss_consumption(
    session: Session, target_datetime: datetime, logger: Logger
):
    """Returns the total consumption of Switzerland."""
    consumptions = ENTSOE.fetch_consumption(
        zone_key="CH", session=session, target_datetime=target_datetime, logger=logger
    )
    return {c["datetime"]: c["consumption"] for c in consumptions}


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "CH",
    session: Union[Session, None] = None,
    target_datetime: Union[datetime, None] = None,
    logger: Logger = getLogger(__name__),
):
    """
    Returns the total production by type for Switzerland.
    Currently the majority of the run-of-river production is missing.
    The difference between the sum of all production types and the total production is allocated as 'unknown'.
    The total production is calculated as sum of the consumption, storage and net imports.
    """
    now = (
        arrow.get(target_datetime).to("Europe/Zurich")
        if target_datetime
        else arrow.now(tz="Europe/Zurich")
    )
    r = session or Session()

    exchanges = fetch_swiss_exchanges(r, now, logger)
    consumptions = fetch_swiss_consumption(r, now, logger)
    productions = ENTSOE.fetch_production(
        zone_key=zone_key, session=r, target_datetime=now, logger=logger
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
