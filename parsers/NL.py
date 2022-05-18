#!/usr/bin/env python3
import logging
import math
from copy import copy
from datetime import datetime, timedelta

import arrow
import numpy as np
import pandas as pd
import requests

from parsers.lib.config import refetch_frequency

from . import DK, ENTSOE, statnett


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="NL",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if target_datetime is None:
        target_datetime = arrow.utcnow()
    else:
        target_datetime = arrow.get(target_datetime)
    r = session or requests.session()

    consumptions = ENTSOE.fetch_consumption(
        zone_key=zone_key, session=r, target_datetime=target_datetime, logger=logger
    )
    if not consumptions:
        return
    for c in consumptions:
        del c["source"]
    df_consumptions = pd.DataFrame.from_dict(consumptions).set_index("datetime")

    # NL has exchanges with BE, DE, NO, GB, DK-DK1
    exchanges = []
    for exchange_key in ["BE", "DE", "GB"]:
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

    # add NO data, fetch once for every hour
    # This introduces an error, because it doesn't use the average power flow
    # during the hour, but rather only the value during the first minute of the
    # hour!
    zone_1, zone_2 = sorted(["NO", zone_key])
    exchange_NO = [
        statnett.fetch_exchange(
            zone_key1=zone_1,
            zone_key2=zone_2,
            session=r,
            target_datetime=dt.datetime,
            logger=logger,
        )
        for dt in arrow.Arrow.range(
            "hour",
            arrow.get(min([e["datetime"] for e in exchanges])).replace(minute=0),
            arrow.get(max([e["datetime"] for e in exchanges])).replace(minute=0),
        )
    ]
    exchanges.extend(exchange_NO)

    # add DK1 data (only for dates after operation)
    if target_datetime > arrow.get("2019-08-24", "YYYY-MM-DD"):
        zone_1, zone_2 = sorted(["DK-DK1", zone_key])
        df_dk = pd.DataFrame(
            DK.fetch_exchange(
                zone_key1=zone_1,
                zone_key2=zone_2,
                session=r,
                target_datetime=target_datetime,
                logger=logger,
            )
        )

        # Because other exchanges and consumption data is only available per hour
        # we floor the timpstamp to hour and group by hour with averaging of netFlow
        df_dk["datetime"] = df_dk["datetime"].dt.floor("H")
        exchange_DK = (
            df_dk.groupby(["datetime"])
            .aggregate({"netFlow": "mean", "sortedZoneKeys": "max", "source": "max"})
            .reset_index()
        )

        # because averaging with high precision numbers leads to rounding errors
        exchange_DK = exchange_DK.round({"netFlow": 3})

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

    df_exchanges = pd.DataFrame.from_dict(exchanges).set_index("datetime")
    # Sum all exchanges to NL imports
    df_exchanges = df_exchanges.groupby("datetime").sum()

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
        if not "unknown" in p["production"] or p["production"]["unknown"] == None:
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
            and Z < df_total_generations[p["datetime"]]
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
            "solar": get_solar_capacity_at(p["datetime"], solar_capacity_df),
            "wind": get_wind_capacity_at(p["datetime"], wind_capacity_df),
        }

    # Filter invalid
    # We should probably add logging to this
    return [p for p in productions if p["production"]["unknown"] > 0]


def fetch_production_energieopwek_nl(
    session=None, target_datetime=None, logger=logging.getLogger(__name__)
) -> list:
    if target_datetime is None:
        target_datetime = arrow.utcnow()

    # Get production values for target and target-1 day
    df_current = get_production_data_energieopwek(target_datetime, session=session)
    df_previous = get_production_data_energieopwek(
        target_datetime.shift(days=-1), session=session
    )

    # Concat them, oldest first to keep chronological order intact
    df = pd.concat([df_previous, df_current])

    output = []
    base_time = (
        arrow.get(target_datetime.date(), "Europe/Paris").shift(days=-1).to("utc")
    )

    for i, prod in enumerate(df.to_dict(orient="records")):
        output.append(
            {
                "zoneKey": "NL",
                "datetime": base_time.shift(minutes=i * 15).datetime,
                "production": prod,
                "source": "energieopwek.nl, entsoe.eu",
            }
        )
    return output


def get_production_data_energieopwek(date, session=None):
    r = session or requests.session()

    # The API returns values per day from local time midnight until the last
    # round 10 minutes if the requested date is today or for the entire day if
    # it's in the past. 'sid' can be anything.
    url = "http://energieopwek.nl/jsonData.php?sid=2ecde3&Day=%s" % date.format(
        "YYYY-MM-DD"
    )
    response = r.get(url)
    obj = response.json()
    production_input = obj["TenMin"]["Country"]

    # extract the power values in kW from the different production types
    # we only need column 0, 1 and 3 contain energy sum values
    df_solar = (
        pd.DataFrame(production_input["Solar"])
        .drop(["1", "3"], axis=1)
        .astype(int)
        .rename(columns={"0": "solar"})
    )
    df_offshore = (
        pd.DataFrame(production_input["WindOffshore"])
        .drop(["1", "3"], axis=1)
        .astype(int)
    )
    df_onshore = (
        pd.DataFrame(production_input["Wind"]).drop(["1", "3"], axis=1).astype(int)
    )

    # We don't differentiate between onshore and offshore wind so we sum them
    # toghether and build a single data frame with named columns
    df_wind = df_onshore.add(df_offshore).rename(columns={"0": "wind"})
    df = pd.concat([df_solar, df_wind], axis=1)

    # resample from 10min resolution to 15min resolution to align with ENTSOE data
    # we duplicate every row and then group them per 3 and take the mean
    df = (
        pd.concat([df] * 2)
        .sort_index(axis=0)
        .reset_index(drop=True)
        .groupby(by=lambda x: math.floor(x / 3))
        .mean()
    )

    # Convert kW to MW with kW resolution
    df = df.apply(lambda x: round(x / 1000, 3))

    return df


def get_wind_capacity_at(date: datetime, wind_capacity_df: pd.DataFrame) -> float:
    in_service_mask = (
        (wind_capacity_df["Start date"] <= date)
        & (date <= wind_capacity_df["End date"])
    ) | (
        (wind_capacity_df["Start date"] <= date)
        & (wind_capacity_df["End date"].isnull())
    )
    return (
        np.array(
            wind_capacity_df[in_service_mask]["#"]
            * wind_capacity_df[in_service_mask].kW
        ).sum()
        / 1000
    )


def get_wind_capacities() -> pd.DataFrame:
    url_wind_capacities = "https://windstats.nl/windstats1/ajax/statsJSON.cfm?minKW=0&maxKW=999999&gemeente=&provincie="
    r = requests.get(url_wind_capacities)
    installations_df = pd.DataFrame(
        columns=[
            "Project",
            "#",
            "Brand",
            "kW",
            "Municipality",
            "Province",
            "Start date",
            "End date",
        ]
    )
    all_installations_data = r.json()["dataList"]
    for row in all_installations_data:
        entry = {
            "Project": row[0].split(">")[1].split("</a")[0],
            "#": row[1],
            "Brand": row[2],
            "kW": row[3],
            "Municipality": row[4],
            "Province": row[5],
            "Start date": row[6],
            "End date": row[8],
        }
        installations_df = installations_df.append(entry, ignore_index=True)
    installations_df.kW = installations_df.kW.astype(float)
    installations_df["#"] = installations_df["#"].astype(int)
    installations_df["Start date"] = pd.to_datetime(
        installations_df["Start date"]
    ).dt.tz_localize("utc")
    installations_df["End date"] = pd.to_datetime(
        installations_df["End date"]
    ).dt.tz_localize("utc")
    return installations_df


def get_solar_capacity_at(date: datetime, solar_capacity_df: pd.DataFrame) -> float:
    latest_year = date.year
    while True:
        # Latest capacity for the year to date might not have been published yet, so revert back to latest known year
        if solar_capacity_df[solar_capacity_df.index.year == latest_year][
            "capacity (MW)"
        ].empty:
            latest_year -= 1
        else:
            return float(
                solar_capacity_df[solar_capacity_df.index.year == latest_year][
                    "capacity (MW)"
                ][0]
            )


def get_solar_capacities() -> pd.DataFrame:
    solar_capacity_base_url = "https://opendata.cbs.nl/ODataApi/odata/82610ENG/UntypedDataSet?$filter=((EnergySourcesTechniques+eq+%27E006590+%27))+and+("

    START_YEAR = 2010
    end_year = arrow.now().year

    years = list(range(START_YEAR, end_year + 1))
    url_solar_capacity = copy(solar_capacity_base_url)

    for i, year in enumerate(years):
        if i == len(years) - 1:
            url_solar_capacity += f"(Periods+eq+%27{year}JJ00%27))"
        else:
            url_solar_capacity += f"(Periods+eq+%27{year}JJ00%27)+or+"

    r = requests.get(url_solar_capacity)

    solar_capacity_df = pd.DataFrame(columns=["datetime", "capacity (MW)"])
    for yearly_row in r.json()["value"]:
        capacity = float(yearly_row["ElectricalCapacityEndOfYear_8"])
        datetime = arrow.get(yearly_row["Periods"].split("JJ")[0]).format()
        solar_capacity_df = solar_capacity_df.append(
            {"datetime": datetime, "capacity (MW)": capacity}, ignore_index=True
        )
    solar_capacity_df.datetime = pd.to_datetime(solar_capacity_df.datetime)
    solar_capacity_df = solar_capacity_df.set_index("datetime")

    return solar_capacity_df


if __name__ == "__main__":
    print(fetch_production())
