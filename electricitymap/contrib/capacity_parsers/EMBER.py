import io
from datetime import datetime
from logging import getLogger
from typing import Any

import pandas as pd
import pycountry
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES

""" Collects capacity data from the yearly electricity data from Ember. The data and documentation can be found here: https://ember-climate.org/data-catalogue/yearly-electricity-data/"""
logger = getLogger(__name__)
EMBER_VARIABLE_TO_MODE = {
    "Bioenergy": "biomass",
    "Coal": "coal",
    "Gas": "gas",
    "Hydro": "hydro",
    "Nuclear": "nuclear",
    "Other Fossil": "unknown",  # mostly oil it seems
    "Other Renewables": "unknown",
    "Solar": "solar",
    "Wind": "wind",
}
EMBER_URL = "https://ember-climate.org"
SOURCE = "Ember, Yearly electricity data"
SPECIFIC_MODE_MAPPING = {
    "AR": {"Other Fossil": "unknown", "Gas": "unknown", "Coal": "unknown"},
    "BD": {"Other Fossil": "oil"},
    "BO": {"Other Fossil": "unknown", "Gas": "unknown"},
    "CO": {"Other Fossil": "oil"},
    "CR": {"Other Fossil": "oil", "Other Renewables": "geothermal"},
    "CY": {"Other Fossil": "oil"},
    "IE": {"Other Fossil": "oil"},
    "KR": {"Other Fossil": "oil"},
    "KW": {"Other Fossil": "oil"},
    "MN": {"Other Fossil": "coal"},
    "NZ": {"Other Renewables": "geothermal"},
    "SG": {"Other Fossil": "coal"},
    "SV": {"Other Renewables": "geothermal", "Gas": "unknown"},
    "TR": {"Other Fossil": "oil", "Other Renewables": "geothermal"},
    "TW": {"Other Fossil": "oil"},
    "UY": {"Other Fossil": "unknown", "Gas": "unknown"},
    "ZA": {"Other Fossil": "oil"},
}

EMBER_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["EMBER"]


def map_variable_to_mode(data: pd.Series) -> str:
    zone = data["zone_key"]
    variable = data["variable"]
    if zone in SPECIFIC_MODE_MAPPING and variable in SPECIFIC_MODE_MAPPING[zone]:
        return SPECIFIC_MODE_MAPPING[zone][variable]
    else:
        return EMBER_VARIABLE_TO_MODE[variable]


def get_data_from_url(session: Session) -> pd.DataFrame:
    # The page where the link below has been found: https://ember-energy.org/data/yearly-electricity-data/
    yearly_catalogue_url = "https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/yearly_full_release_long_format.csv"

    r_csv: Response = session.get(yearly_catalogue_url)
    df = pd.read_csv(io.StringIO(r_csv.text))
    return df


def format_ember_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    df_filtered = df.loc[df["Area type"] == "Country"].copy()
    df_filtered = df_filtered.loc[df_filtered["Year"] == year]
    if df_filtered.empty:
        raise ValueError(f"No data for year {year}")
    df_filtered = df_filtered.loc[
        (df_filtered["Category"] == "Capacity") & (df_filtered["Subcategory"] == "Fuel")
    ]
    # filter out Kosovo because it is not a country in pycountry
    df_filtered = df_filtered.loc[df_filtered["Area"] != "Kosovo"]

    df_filtered["country_code_iso2"] = df_filtered["Country code"].apply(
        lambda x: pycountry.countries.get(alpha_3=x).alpha_2
    )
    df_filtered = df_filtered.loc[df_filtered["country_code_iso2"].isin(EMBER_ZONES)]

    df_capacity = df_filtered[["country_code_iso2", "Year", "Variable", "Value"]]
    df_capacity = df_capacity.rename(
        columns={
            "country_code_iso2": "zone_key",
            "Year": "datetime",
            "Variable": "variable",
            "Value": "value",
        }
    )
    df_capacity["datetime"] = df_capacity["datetime"].apply(lambda x: datetime(x, 1, 1))
    df_capacity["value"] = df_capacity["value"] * 1000  # convert from GW to MW

    df_capacity["mode"] = df_capacity.apply(map_variable_to_mode, axis=1)
    df_capacity = df_capacity.dropna(subset=["value"])

    df_capacity = (
        df_capacity.groupby(["zone_key", "datetime", "mode"])[["value"]]
        .sum()
        .reset_index()
        .set_index(["zone_key"])
    )
    return df_capacity


def get_capacity_dict_from_df(df_capacity: pd.DataFrame) -> dict[str, Any]:
    all_capacity = {}
    for zone in df_capacity.index.unique():
        df_zone = df_capacity.loc[zone]
        zone_capacity = {}
        for _i, data in df_zone.iterrows():
            mode_capacity = {}
            mode_capacity["datetime"] = data["datetime"].strftime("%Y-%m-%d")
            mode_capacity["value"] = round(float(data["value"]), 0)
            mode_capacity["source"] = SOURCE
            zone_capacity[data["mode"]] = mode_capacity
        all_capacity[zone] = zone_capacity
    return all_capacity


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session
) -> dict[str, Any]:
    df_capacity = get_data_from_url(session)
    df_capacity = format_ember_data(df_capacity, target_datetime.year)
    all_capacity = get_capacity_dict_from_df(df_capacity)
    logger.info(f"Fetched capacity data from Ember for {target_datetime.year}")
    return all_capacity


def fetch_production_capacity(
    target_datetime: datetime, zone_key: ZoneKey, session: Session
) -> dict[str, Any] | None:
    all_capacity = fetch_production_capacity_for_all_zones(target_datetime, session)
    if zone_key in all_capacity:
        zone_capacity = all_capacity[zone_key]
        logger.info(
            f"Fetched capacity for {zone_key} in {target_datetime.year}: \n {zone_capacity}"
        )
        return zone_capacity
    else:
        logger.warning(f"No capacity data for {zone_key} in {target_datetime.year}")


if __name__ == "__main__":
    session = Session()
    print(
        fetch_production_capacity(
            zone_key="CO", target_datetime=datetime(2020, 1, 1), session=session
        )
    )
