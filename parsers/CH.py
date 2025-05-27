from datetime import UTC, datetime, timedelta
from io import StringIO
from logging import Logger, getLogger

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENTSOE
from parsers.lib.config import refetch_frequency


def get_solar_capacity_at(target_datetime: datetime) -> float:
    """Returns the solar capacity (in MW) at a given time.

    References:
        https://www.uvek-gis.admin.ch/BFE/storymaps/EE_Elektrizitaetsproduktionsanlagen/?lang=en
        https://www.uvek-gis.admin.ch/BFE/storymaps/EE_Elektrizitaetsproduktionsanlagen/data/solar.csv
    """

    # Prepare historical records
    # Values before 2015 are ignored as that is the absolute earliest we have some confidence in the data we are
    # collecting and flowtracing (2015 is when the ENTSO-E transparency platform launched).
    historical_data = """
        Power_sum,Year,Plant_count
        1398.217,2015,46162
        1656.707,2016,56830
        1875.034,2017,70074
        2107.374,2018,83239
        2398.745,2019,97776
        2831.102,2020,117258
        3370.261,2021,140428
        4080.415,2022,173068
        5094.375,2023,216440
        5108.034,2024,216918
        """

    historical_capacities = pd.read_csv(
        StringIO(historical_data),
        names=["installed capacity in megawatts", "year", "number of plants"],
        header=0,
        index_col=["year"],
    )
    historical_capacities.index = pd.to_datetime(
        historical_capacities.index, format="%Y", utc=True
    )

    # mask all rows earlier than target date (use the earliest date in dataset if target date is even earlier)
    dt = max(target_datetime.astimezone(UTC), historical_capacities.index.min())
    mask = historical_capacities.index <= dt
    return historical_capacities[mask].iloc[-1].loc["installed capacity in megawatts"]


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
        datetime.now(UTC)
        if target_datetime is None
        else target_datetime.astimezone(UTC)
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
