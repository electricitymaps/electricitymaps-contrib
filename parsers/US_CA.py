#!/usr/bin/env python3

from collections import defaultdict
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional, Union

import arrow
import numpy as np
import pandas
import pytz
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from parsers.lib.config import refetch_frequency
from parsers.lib.validation import validate_consumption

CAISO_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
PRODUCTION_URL_REAL_TIME = f"{CAISO_PROXY}/outlook/SP/fuelsource.csv?host=https://www.caiso.com"
DEMAND_URL_REAL_TIME = f"{CAISO_PROXY}/outlook/SP/netdemand.csv?host=https://www.caiso.com"

HISTORICAL_URL_MAPPING = {"production":"fuelsource", "consumption":"netdemand"}
REAL_TIME_URL_MAPPING = {"production":PRODUCTION_URL_REAL_TIME, "consumption":DEMAND_URL_REAL_TIME}

PRODUCTION_MODES_MAPPING = {
    "Solar": "solar",
    "Wind": "wind",
    "Geothermal": "geothermal",
    "Biomass": "biomass",
    "Biogas": "biomass",
    "Small hydro": "hydro",
    "Coal": "coal",
    "Nuclear": "nuclear",
    "Natural Gas": "gas",
    "Large Hydro": "hydro",
    "Other": "unknown",
}
STORAGE_MAPPING = {"Batteries": "battery"}

MX_EXCHANGE_URL = "http://www.cenace.gob.mx/Paginas/Publicas/Info/DemandaRegional.aspx"

def get_target_url(target_datetime:datetime, kind: str)->str:
    if target_datetime is None:
        target_datetime = datetime.now(tz=pytz.UTC)
        target_url = REAL_TIME_URL_MAPPING[kind]
    else:
        target_url = f"{CAISO_PROXY}/outlook/SP/History/{target_datetime.strftime('%Y%m%d')}/{HISTORICAL_URL_MAPPING[kind]}.csv?host=https://www.caiso.com"
    return target_url

@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "US-CA",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    target_url = get_target_url(target_datetime, kind="production")

    if target_datetime is None:
        target_datetime = arrow.now(tz="US/Pacific").floor("day").datetime

    # Get the production from the CSV
    csv = pandas.read_csv(target_url)

    # Filter out last row if timestamp is 00:00
    if  csv.iloc[-1]["Time"] =="OO:OO":
        df = csv.copy().iloc[:-1]
    else:
        df = csv.copy()
    df = df.rename(columns={**PRODUCTION_MODES_MAPPING, **STORAGE_MAPPING})
    df = df.groupby(level=0, axis=1).sum()

    all_data_points = []
    for index, row in df.iterrows():
        production = {}
        storage = {}

        row_datetime = target_datetime.replace(hour= int(row["Time"][:2]), minute=int(row["Time"][-2:]))
        for mode in [mode for mode in PRODUCTION_MODES if mode in row]:
            production_value =  float(row[mode])
            if production_value < 0 and (
                mode in  ["solar", "nuclear", "coal","gas","unknown","biomass"]
            ):
                logger.warn(
                    f" {mode} production for US_CA was reported as less than 0 and was clamped"
                )
                production_value = 0.0

            production[mode] = production_value

        storage["battery"] = float(row["battery"])

        data = {
            "zoneKey": zone_key,
            "production": production,
            "storage": storage,
            "source": "caiso.com",
            "datetime": arrow.get(row_datetime).replace(tzinfo="US/Pacific").datetime,
        }
        all_data_points.append(data)
    return all_data_points

@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "US-CA",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""

    target_url = get_target_url(target_datetime, kind="consumption")

    if target_datetime is None:
        target_datetime = arrow.now(tz="US/Pacific").floor("day").datetime


    # Get the demand from the CSV
    csv = pandas.read_csv(target_url)

    # Filter out last row if timestamp is 00:00
    if  csv.iloc[-1]["Time"] =="OO:OO":
        df = csv.copy().iloc[:-1]
    else:
        df = csv.copy()

    all_data_points = []
    for row in df.itertuples():
        consumption= row._3
        row_datetime = target_datetime.replace(hour= int(row.Time[:2]), minute=int(row.Time[-2:]))
        if not np.isnan(consumption):
            data_point = {
                "zoneKey": zone_key,
                "consumption": consumption,
                "source": "caiso.com",
                "datetime":  arrow.get(row_datetime).replace(tzinfo="US/Pacific").datetime
            }
            all_data_points.append(data_point)

    validated_data_points = [validate_consumption(datapoint, logger) for datapoint in all_data_points]
    return validated_data_points


def fetch_MX_exchange(s: Session) -> float:
    req = s.get(MX_EXCHANGE_URL)
    soup = BeautifulSoup(req.text, "html.parser")
    exchange_div = soup.find("div", attrs={"id": "IntercambioUSA-BCA"})
    val = exchange_div.text

    # cenace html uses unicode hyphens instead of minus signs
    try:
        val = val.replace(chr(8208), chr(45))
    except ValueError:
        pass

    # negative value indicates flow from CA to MX

    return float(val)


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    s = session or Session()

    if sorted_zone_keys == "MX-BC->US-CA" or sorted_zone_keys == "MX-BC->US-CAL-CISO":
        netflow = fetch_MX_exchange(s)
        exchange = {
            "sortedZoneKeys": sorted_zone_keys,
            "datetime": arrow.now("America/Tijuana").datetime,
            "netFlow": netflow,
            "source": "cenace.gob.mx",
        }
        return exchange

    # CSV has imports to California as positive.
    # Electricity Map expects A->B to indicate flow to B as positive.
    # So values in CSV can be used as-is.
    target_url = get_target_url(target_datetime, kind="production")
    csv = pandas.read_csv(target_url)
    latest_index = len(csv) - 1
    daily_data = []
    for i in range(0, latest_index + 1):
        h, m = map(int, csv["Time"][i].split(":"))
        date = (
            arrow.utcnow()
            .to("US/Pacific")
            .replace(hour=h, minute=m, second=0, microsecond=0)
        )
        data = {
            "sortedZoneKeys": sorted_zone_keys,
            "datetime": date.datetime,
            "netFlow": float(csv["Imports"][i]),
            "source": "caiso.com",
        }

        daily_data.append(data)

    return daily_data


if __name__ == "__main__":
    "Main method, not used by Electricity Map backend, but handy for testing"

    from pprint import pprint

    print("fetch_production() ->")
    # pprint(fetch_production(target_datetime=datetime(2023,1,20)))s
    pprint(fetch_consumption(target_datetime=datetime(2022,2,22)))


