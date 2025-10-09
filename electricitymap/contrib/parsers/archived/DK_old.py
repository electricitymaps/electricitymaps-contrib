# Archived reason: The SQL API is no longer available and a new DK parser was created.
import json
import time
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

import arrow  # the arrow library is used to handle datetimes
import pandas as pd
from requests import Session, exceptions

from electricitymap.contrib.parsers.lib.config import refetch_frequency

from .lib.exceptions import ParserException

ids = {
    "real_time": "06380963-b7c6-46b7-aec5-173d15e4648b",
    "energy_bal": "02356e88-7c4e-4ee9-b896-275d217cc1b9",
}


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "DK-DK1",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """
    Queries "Electricity balance Non-Validated" from energinet api
    for Danish bidding zones

    NOTE: Missing historical wind/solar data @ 2017-08-01
    """
    r = session or Session()

    if zone_key not in ["DK-DK1", "DK-DK2"]:
        raise NotImplementedError(f"fetch_production() for {zone_key} not implemented")

    zone = zone_key[-3:]

    timestamp = arrow.get(target_datetime).strftime("%Y-%m-%d %H:%M")

    # fetch hourly energy balance from recent hours
    sqlstr = 'SELECT "HourUTC" as timestamp, "Biomass", "Waste", \
                     "OtherRenewable", "FossilGas" as gas, "FossilHardCoal" as coal, \
                     "FossilOil" as oil, "HydroPower" as hydro, \
                     ("OffshoreWindPower"%2B"OnshoreWindPower") as wind, \
                     "SolarPower" as solar from "{0}" \
                     WHERE "PriceArea" = \'{1}\' AND \
                     "HourUTC" >= (timestamp\'{2}\'-INTERVAL \'24 hours\') AND \
                     "HourUTC" <= timestamp\'{2}\' \
                     ORDER BY "HourUTC" ASC'.format(ids["energy_bal"], zone, timestamp)

    url = f"https://api.energidataservice.dk/datastore_search_sql?sql={sqlstr}"
    response = r.get(url)

    # raise errors for responses with an error or no data
    retry_count = 0
    while response.status_code in [429, 403, 500]:
        retry_count += 1
        if retry_count > 5:
            raise Exception("Retried too many times..")
        # Wait and retry
        logger.warn("Retrying..")
        time.sleep(5**retry_count)
        response = r.get(url)
    if response.status_code != 200:
        j = response.json()
        if "error" in j and "info" in j["error"]:
            error = j["error"]["__type"]
            text = j["error"]["info"]["orig"]
            msg = f'"{error}" fetching production data for {zone_key}: {text}'
        else:
            msg = "error while fetching production data for {}: {}".format(
                zone_key, json.dumps(j)
            )
        exceptions.HTTPError(msg)
    if not response.json()["result"]["records"]:
        raise ParserException("DK.py", "API returned no data", zone_key=zone_key)

    df = pd.DataFrame(response.json()["result"]["records"])
    # index response dataframe by time
    df = df.set_index("timestamp")
    df.index = pd.DatetimeIndex(df.index)
    # drop empty rows from energy balance
    df.dropna(how="all", inplace=True)

    # Divide waste into 55% renewable and 45% non-renewable parts according to
    # https://ens.dk/sites/ens.dk/files/Statistik/int.reporting_2016.xls (visited Jan 24th, 2019)
    df["unknown"] = 0.45 * df["Waste"]  # Report fossil waste as unknown
    df["renwaste"] = 0.55 * df["Waste"]
    # Report biomass, renewable waste and other renewables (biogas etc.) as biomass
    df["biomass"] = df.filter(["Biomass", "renwaste", "OtherRenewable"]).sum(axis=1)

    fuels = ["biomass", "coal", "oil", "gas", "unknown", "hydro"]
    # Format output as a list of dictionaries
    output = []
    for dt in df.index:
        data = {
            "zoneKey": zone_key,
            "datetime": None,
            "production": {
                "biomass": 0,
                "coal": 0,
                "gas": 0,
                "hydro": None,
                "nuclear": 0,
                "oil": 0,
                "solar": None,
                "wind": None,
                "geothermal": None,
                "unknown": 0,
            },
            "storage": {},
            "source": "api.energidataservice.dk",
        }

        data["datetime"] = dt.to_pydatetime()
        data["datetime"] = data["datetime"].replace(tzinfo=timezone.utc)
        for f in ["solar", "wind"] + fuels:
            data["production"][f] = df.loc[dt, f]
        output.append(data)
    return output


def fetch_exchange(
    zone_key1: str = "DK-DK1",
    zone_key2: str = "DK-DK2",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """
    Fetches 5-minute frequency exchange data for Danish bidding zones
    from api.energidataservice.dk
    """
    r = session or Session()
    sorted_keys = "->".join(sorted([zone_key1, zone_key2]))

    # pick the correct zone to search
    if "DK1" in sorted_keys and "DK2" in sorted_keys:
        zone = "DK1"
    elif "DK1" in sorted_keys:
        zone = "DK1"
    elif "DK2" in sorted_keys:
        zone = "DK2"
    elif "DK-BHM" in sorted_keys:
        zone = "DK2"
    else:
        raise NotImplementedError(
            "Only able to fetch exchanges for Danish bidding zones"
        )

    exch_map = {
        "DE->DK-DK1": '"ExchangeGermany"',
        "DE->DK-DK2": '"ExchangeGermany"',
        "DK-DK1->DK-DK2": '"ExchangeGreatBelt"',
        "DK-DK1->NO-NO2": '"ExchangeNorway"',
        "DK-DK1->NL": '"ExchangeNetherlands"',
        "DK-DK1->SE": '"ExchangeSweden"',
        "DK-DK1->SE-SE3": '"ExchangeSweden"',
        "DK-DK1->NL": '"ExchangeNetherlands"',
        "DK-DK2->SE": '("ExchangeSweden" - "BornholmSE4")',  # Exchange from Bornholm to Sweden is included in "ExchangeSweden"
        "DK-DK2->SE-SE4": '("ExchangeSweden" - "BornholmSE4")',  # but Bornholm island is reported separately from DK-DK2 in eMap
        "DK-BHM->SE-SE4": '"BornholmSE4"',
    }
    if sorted_keys not in exch_map:
        raise NotImplementedError(f"Exchange {sorted_keys} not implemented")

    timestamp = arrow.get(target_datetime).strftime("%Y-%m-%d %H:%M")

    # fetch real-time/5-min data
    sqlstr = 'SELECT "Minutes5UTC" as timestamp, {0} as "netFlow" \
                     from "{1}" WHERE "PriceArea" = \'{2}\' AND \
                     "Minutes5UTC" >= (timestamp\'{3}\'-INTERVAL \'24 hours\') AND \
                     "Minutes5UTC" <= timestamp\'{3}\' \
                     ORDER BY "Minutes5UTC" ASC'.format(
        exch_map[sorted_keys], ids["real_time"], zone, timestamp
    )

    url = f"https://api.energidataservice.dk/datastore_search_sql?sql={sqlstr}"
    response = r.get(url)

    # raise errors for responses with an error or no data
    retry_count = 0
    while response.status_code in [429, 403, 500]:
        retry_count += 1
        if retry_count > 5:
            raise Exception("Retried too many times..")
        # Wait and retry
        logger.warn("Retrying..")
        time.sleep(5**retry_count)
        response = r.get(url)
    if response.status_code != 200:
        j = response.json()
        if "error" in j and "info" in j["error"]:
            error = j["error"]["__type"]
            text = j["error"]["info"]["orig"]
            msg = f'"{error}" fetching exchange data for {sorted_keys}: {text}'
        else:
            msg = "error while fetching exchange data for {}: {}".format(
                sorted_keys, json.dumps(j)
            )
        raise exceptions.HTTPError(msg)
    if not response.json()["result"]["records"]:
        raise ParserException("DK.py", "API returned no data", zone_key=sorted_keys)

    df = pd.DataFrame(response.json()["result"]["records"])
    df = df.set_index("timestamp")
    df.index = pd.DatetimeIndex(df.index)
    # drop empty rows
    df.dropna(how="all", inplace=True)

    # all exchanges are reported as net import,
    # where as eMap expects net export from
    # the first zone in alphabetical order
    if "DE" not in sorted_keys:
        df["netFlow"] = -1 * df["netFlow"]
    # Format output
    output = []
    for dt in df.index:
        data = {
            "sortedZoneKeys": sorted_keys,
            "datetime": None,
            "netFlow": None,
            "source": "api.energidataservice.dk",
        }

        data["datetime"] = dt.to_pydatetime()
        data["datetime"] = data["datetime"].replace(tzinfo=timezone.utc)
        data["netFlow"] = df.loc[dt, "netFlow"]
        output.append(data)
    return output


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(DK-DK2, SE-SE4) ->")
    print(fetch_exchange("DK-DK2", "SE-SE4"))
