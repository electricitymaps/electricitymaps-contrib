#!/usr/bin/env python3
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

SOURCE = "taipower.com.tw"
TIMEZONE = ZoneInfo("Asia/Taipei")
PRODUCTION_URL = (
    "http://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary_eng.json"
)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "TW",
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    response = session.get(PRODUCTION_URL)
    if not response.status_code == 200:
        raise ParserException(
            "TW",
            f"Query failed with status code {response.status_code} and {response.content}",
        )

    data = response.json()

    dt = data[""]
    prodData = data["dataset"]

    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M").replace(tzinfo=TIMEZONE)

    objData = pd.DataFrame(prodData)

    columns = [
        "fueltype",
        "additional_1",
        "name",
        "capacity",
        "output",
        "percentage",
        "additional_2",
        "additional_3",
    ]
    assert len(objData.iloc[0]) == len(columns), "number of input columns changed"
    objData.columns = columns
    objData["fueltype"] = objData.fueltype.str.split("<b>").str[1]
    objData["fueltype"] = objData.fueltype.str.split("</b>").str[0]
    objData.loc[:, ["capacity", "output"]] = objData[["capacity", "output"]].apply(
        pd.to_numeric, errors="coerce"
    )
    if objData["fueltype"].str.contains("OTHERRENEWABLEENERGY").any():
        if objData["name"].str.contains("Geothermal").any():
            objData.loc[objData["name"].str.contains("Geothermal"), "fueltype"] = (
                "Geothermal"
            )
        if objData["name"].str.contains("Biofuel").any():
            objData.loc[objData["name"].str.contains("Biofuel"), "fueltype"] = "Biofuel"

    assert (
        not objData.capacity.isna().all()
    ), "capacity data is entirely NaN - input column order may have changed"
    assert (
        not objData.output.isna().all()
    ), "output data is entirely NaN - input column order may have changed"

    objData.drop(
        columns=["additional_1", "name", "additional_2", "percentage", "additional_3"],
        axis=1,
        inplace=True,
    )
    # summing because items in returned object are for each power plant and operational units
    production = pd.DataFrame(objData.groupby("fueltype").sum())
    production.columns = ["capacity", "output"]

    # check output values coincide with total capacity by fuel type
    check_values = production.output <= production.capacity
    modes_with_capacity_exceeded = production[~check_values].index.tolist()
    for mode in modes_with_capacity_exceeded:
        logger.warning(f"Capacity exceeded for {mode} in {zone_key} at {dt}")

    # For storage, note that load will be negative, and generation positive.
    # We require the opposite
    PRODUCTION_MODE_MAPPING = {
        "biomass": ["Biofuel"],
        "coal": ["COAL", "IPPCOAL"],
        "gas": ["LNG", "IPPLNG"],
        "geothermal": ["Geothermal"],
        "oil": ["OIL", "DIESEL"],
        "hydro": ["HYDRO"],
        "nuclear": ["NUCLEAR"],
        "solar": ["SOLAR"],
        "wind": ["WIND"],
        "unknown": ["COGEN"],
    }
    STORAGE_MODE_MAPPING = {
        "hydro": ["PUMPINGLOAD", "PUMPINGGEN"],
    }

    production_breakdown = ProductionBreakdownList(logger)
    production_mix = ProductionMix()
    for mode, parser_modes in PRODUCTION_MODE_MAPPING.items():
        parser_modes_in_df = [
            parser_mode
            for parser_mode in parser_modes
            if parser_mode in production.index
        ]
        production_mix.add_value(mode, production.loc[parser_modes_in_df].output.sum())
    storage_mix = StorageMix()
    for mode, storage_modes in STORAGE_MODE_MAPPING.items():
        storage_modes_in_df = [
            storage_mode
            for storage_mode in storage_modes
            if storage_mode in production.index
        ]
        storage_mix.add_value(
            mode, -1 * production.loc[storage_modes_in_df].output.sum()
        )
    production_breakdown.append(
        zone_key,
        dt,
        SOURCE,
        production_mix,
        storage_mix,
    )

    capacity = {}
    for mode, parser_modes in PRODUCTION_MODE_MAPPING.items():
        parser_modes_in_df = [
            parser_mode
            for parser_mode in parser_modes
            if parser_mode in production.index
        ]
        capacity[mode] = production.loc[parser_modes_in_df].capacity.sum()

    return [{**e, **{"capacity": capacity}} for e in production_breakdown.to_list()]


if __name__ == "__main__":
    print(fetch_production())
