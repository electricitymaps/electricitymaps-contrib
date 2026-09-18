from copy import copy
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

import pandas as pd
from requests import Session, get

from electricitymap.contrib.config import ZONES_CONFIG
from electricitymap.contrib.parsers import DK, ENTSOE
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.types import ZoneKey

ZONE_CONFIG = ZONES_CONFIG["NL"]
UTC = timezone.utc


def _fetch_dk1_exchange(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime,
    logger: Logger,
) -> pd.DataFrame:
    """Fetch the NL<->DK-DK1 exchange covering the full ``[target-1d, target]`` window.

    ``DK.fetch_exchange`` returns a single *calendar day* of 5-min data keyed off
    ``target_datetime``'s date, whereas NL's other inputs (consumption and the
    ENTSOE exchanges) use a rolling 24h window. With a single DK fetch the
    "previous day" hours of NL's output get the DK-DK1 flow on a refetch that
    targets day ``D-1`` but not on one that targets day ``D``, which flips the
    derived ``unknown`` production back and forth (data churn). Fetching both the
    current and previous calendar day guarantees every hour in the rolling window
    has its full set of 5-min points, so the hourly mean is stable across
    refetches.
    """
    zone_1, zone_2 = sorted(["DK-DK1", zone_key])
    records = []
    for day in (target_datetime - timedelta(days=1), target_datetime):
        records.extend(
            DK.fetch_exchange(
                zone_key1=zone_1,
                zone_key2=zone_2,
                session=session,
                target_datetime=day,
                logger=logger,
            )
            or []
        )

    df_dk = pd.DataFrame(records)
    if df_dk.empty:
        return df_dk

    # Adjacent calendar-day fetches can repeat the midnight boundary point.
    df_dk = df_dk.drop_duplicates(subset=["datetime"])

    # Other exchanges and consumption are hourly, so we floor the 5-min flows to
    # the hour and average. Hours are now always complete (see docstring), so the
    # mean no longer depends on where the fetch window edge happened to fall.
    df_dk["datetime"] = df_dk["datetime"].dt.floor("H")
    return (
        df_dk.groupby(["datetime"])
        .aggregate({"netFlow": "mean", "sortedZoneKeys": "max", "source": "max"})
        .reset_index()
        # averaging high-precision numbers leads to rounding errors
        .round({"netFlow": 3})
    )


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("NL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    target_datetime = (
        datetime.now(UTC)
        if target_datetime is None
        else target_datetime.astimezone(UTC)
    )

    r = session or Session()

    consumptions = ENTSOE.fetch_consumption(
        zone_key=zone_key, session=r, target_datetime=target_datetime, logger=logger
    )
    if not consumptions:
        return
    for c in consumptions:
        del c["source"]
    df_consumptions = pd.DataFrame.from_dict(consumptions)
    df_consumptions["datetime"] = df_consumptions["datetime"].apply(
        lambda x: x.replace(tzinfo=UTC)
    )

    # NL has exchanges with BE, DE, NO, GB, DK-DK1
    exchanges = []
    for exchange_key in ["BE", "DE", "GB", "NO-NO2"]:
        zone_1, zone_2 = sorted([exchange_key, zone_key])
        exchange = ENTSOE.fetch_exchange(
            zone_key1=zone_1,
            zone_key2=zone_2,
            session=r,
            target_datetime=target_datetime,
            logger=logger,
        )
        if not exchange:
            return
        exchanges.extend(exchange or [])

    # add DK1 data (only for dates after operation)
    if target_datetime > datetime(2019, 8, 24, tzinfo=UTC):
        exchange_DK = _fetch_dk1_exchange(zone_key, r, target_datetime, logger)
        exchanges.extend(exchange_DK.to_dict(orient="records"))

    # We want to know the net-imports into NL, so if NL is in zone_1 we need
    # to flip the direction of the flow. E.g. 100MW for NL->DE means 100MW
    # export to DE and needs to become -100MW for import to NL.
    for e in exchanges:
        if e["sortedZoneKeys"].startswith("NL->"):
            e["NL_import"] = -1 * e["netFlow"]
        else:
            e["NL_import"] = e["netFlow"]
        del e["source"]
        del e["netFlow"]

    df_exchanges = pd.DataFrame.from_dict(exchanges)
    df_exchanges["datetime"] = df_exchanges["datetime"].apply(
        lambda x: x.replace(tzinfo=UTC)
    )
    # Sum all exchanges to NL imports
    df_exchanges = df_exchanges.groupby("datetime").sum(
        numeric_only=True,
    )

    # Fill missing values by propagating the value forward
    df_consumptions_with_exchanges = df_consumptions.join(df_exchanges).fillna(
        method="ffill", limit=3
    )  # Limit to 3 x 15min

    # Load = Generation + netImports
    # => Generation = Load - netImports
    df_total_generations = (
        df_consumptions_with_exchanges["consumption"]
        - df_consumptions_with_exchanges["NL_import"]
    )

    # Fetch all production
    productions = ENTSOE.fetch_production(
        zone_key=zone_key, session=r, target_datetime=target_datetime, logger=logger
    )
    if not productions:
        return

    # Flatten production dictionaries (we ignore storage)
    for p in productions:
        # if for some reason theré's no unknown value
        if "unknown" not in p["production"] or p["production"]["unknown"] is None:
            p["production"]["unknown"] = 0

        Z = sum([x or 0 for x in p["production"].values()])
        # Only calculate the difference if the datetime exists
        # If total ENTSOE reported production (Z) is less than total generation
        # (calculated from consumption and imports), then there must be some
        # unknown production missing, so we add the difference.
        # The difference can actually be negative, because consumption is based
        # on TSO network load, but locally generated electricity may never leave
        # the DSO network and be substantial (e.g. Solar).
        if (
            p["datetime"] in df_total_generations
            and df_total_generations[p["datetime"]] > Z
        ):
            p["production"]["unknown"] = round(
                (df_total_generations[p["datetime"]] - Z + p["production"]["unknown"]),
                3,
            )

    # Add capacities
    solar_capacity_df = get_solar_capacities()
    wind_capacity_df = get_wind_capacities()
    for p in productions:
        p["capacity"] = {
            "solar": round(get_solar_capacity_at(p["datetime"], solar_capacity_df), 3),
            "wind": round(get_wind_capacity_at(p["datetime"], wind_capacity_df), 3),
        }

    # Filter invalid
    # We should probably add logging to this
    return [p for p in productions if p["production"]["unknown"] > 0]


def get_wind_capacities() -> pd.DataFrame:
    url_wind_capacities = "https://api.windstats.nl/stats"

    capacities_df = pd.DataFrame(columns=["datetime", "capacity (MW)"])
    try:
        r = get(url_wind_capacities)
        per_year_split_capacity = r.json()["combinedPowerPerYearSplitByLandAndSea"]
    except Exception as e:
        Logger.error(f"Error fetching wind capacities: {e}")
        return capacities_df

    per_year_capacity = {
        f"{year}-01-01 00:00:00+00:00": sum(split.values())
        for (year, split) in per_year_split_capacity.items()
    }

    capacities_df["datetime"] = pd.to_datetime(list(per_year_capacity.keys()))
    capacities_df["capacity (MW)"] = list(per_year_capacity.values())
    capacities_df = capacities_df.set_index("datetime")

    return capacities_df


def get_solar_capacities() -> pd.DataFrame:
    solar_capacity_base_url = "https://opendata.cbs.nl/ODataApi/odata/82610ENG/UntypedDataSet?$filter=((EnergySourcesTechniques+eq+%27E006590+%27))+and+("

    START_YEAR = 2010
    end_year = datetime.now(UTC).year

    years = list(range(START_YEAR, end_year + 1))
    url_solar_capacity = copy(solar_capacity_base_url)

    for i, year in enumerate(years):
        if i == len(years) - 1:
            url_solar_capacity += f"(Periods+eq+%27{year}JJ00%27))"
        else:
            url_solar_capacity += f"(Periods+eq+%27{year}JJ00%27)+or+"

    solar_capacity_df = pd.DataFrame(columns=["datetime", "capacity (MW)"])

    try:
        r = get(url_solar_capacity)
        per_year_capacity = r.json()["value"]
    except Exception as e:
        Logger.error(f"Error fetching solar capacities: {e}")
        return solar_capacity_df

    for yearly_row in per_year_capacity:
        capacity = float(yearly_row["ElectricalCapacityEndOfYear_8"])
        year = yearly_row["Periods"].split("JJ")[0]
        dt = datetime(int(year), 1, 1, tzinfo=UTC)
        solar_capacity_df = solar_capacity_df.append(
            {"datetime": dt, "capacity (MW)": capacity}, ignore_index=True
        )
    solar_capacity_df = solar_capacity_df.set_index("datetime")

    return solar_capacity_df


def _get_capacity_at(date: datetime, mode: str, capacity_df: pd.DataFrame) -> float:
    assert mode in ["solar", "wind"]
    default_capacity = ZONE_CONFIG["capacity"][mode]
    if capacity_df.empty:
        return default_capacity
    latest_year = date.year
    while latest_year > 2015:
        # Latest capacity for the year to date might not have been published yet, so revert back to latest known year
        if capacity_df[capacity_df.index.year == latest_year]["capacity (MW)"].empty:
            latest_year -= 1
        else:
            return float(
                capacity_df[capacity_df.index.year == latest_year]["capacity (MW)"][0]
            )
    return default_capacity


def get_solar_capacity_at(date: datetime, solar_capacity_df: pd.DataFrame) -> float:
    return _get_capacity_at(date, "solar", solar_capacity_df)


def get_wind_capacity_at(date: datetime, wind_capacity_df: pd.DataFrame) -> float:
    return _get_capacity_at(date, "wind", wind_capacity_df)


if __name__ == "__main__":
    print(fetch_production())
