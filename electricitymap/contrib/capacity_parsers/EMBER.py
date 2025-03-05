import urllib.parse
from datetime import datetime
from logging import getLogger
from typing import Any

import pandas as pd
import pycountry
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.contrib.config.constants import ENERGIES

""" Collects capacity data from the yearly electricity data from Ember. The data and documentation can be found here: https://ember-climate.org/data-catalogue/yearly-electricity-data/"""
logger = getLogger(__name__)
EMBER_URL = "https://ember-climate.org"
SOURCE = "Ember, Yearly electricity data"
SPECIFIC_MODE_MAPPING = {
    "AR": {"other fossil": "unknown"},
    "BD": {"other fossil": "oil"},
    "BO": {"other fossil": "unknown"},
    "CO": {"other fossil": "oil"},
    "CR": {"other fossil": "oil", "other renewables": "geothermal"},
    "CY": {"other fossil": "oil"},
    "IE": {"other fossil": "oil"},
    "KR": {"other fossil": "oil"},
    "KW": {"other fossil": "oil"},
    "MN": {"other fossil": "coal"},
    "NZ": {"other renewables": "geothermal"},
    "SG": {"other fossil": "coal"},
    "SV": {"other renewables": "geothermal"},
    "TR": {"other fossil": "oil", "other renewables": "geothermal"},
    "TW": {"other fossil": "oil"},
    "UY": {"other fossil": "unknown"},
    "ZA": {"other fossil": "oil"},
}

EMBER_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["EMBER"]


def get_ember_yearly_data(country_iso2: ZoneKey | None, year: int = 2017) -> str:
    """
    Creates a URL to fetch generation_yearly data from the API,
    using ISO 3 country code and a year
    ex: 'https://ember-data-api-scg3n.ondigitalocean.app/ember/generation_yearly.json?_sort=rowid&country_code=FRA&year__gte=2017&_shape=array'
    Args:
        country_iso2 (str | None): ISO 2 country code (e.g., "FR").
        year (int, optional): Minimum year to filter data. Defaults to 2017.
    Returns:
        str: The constructed URL.
    """
    generation = "generation_yearly"
    if country_iso2 is None:
        query_params = {"year": year, "_shape": "array"}
    else:
        try:
            iso3_code = pycountry.countries.get(alpha_2=country_iso2).alpha_3
        except AttributeError as err:
            raise ValueError(
                "Invalid ISO 2 country code: Use only ISO 2 country codes (e.g. FR, US, DE, etc. and not DK-DK1)"
            ) from err
        query_params = {"country_code": iso3_code, "year": year, "_shape": "array"}
    base_url = (
        f"https://ember-data-api-scg3n.ondigitalocean.app/ember/{generation}.json"
    )

    encoded_params = urllib.parse.urlencode(query_params)
    full_url = f"{base_url}?{encoded_params}"
    df = pd.read_json(full_url)
    if df.size == 10000:
        raise ValueError(
            "You are only getting the first 10000 records, you need to change the country or year"
        )
    return df


def _ember_production_mode_mapper(row: pd.Series) -> str | None:
    category_col = "mode"

    # Ember also reports the following, which we exclude due to:
    # 'Wind and solar' is contained in 'wind' and 'solar' data
    # 'Fossil' contained in all non-renewable sources, i.e. 'coal', 'gas', 'oil', 'other fossil
    # 'Clean' containd in all renewable sources, i.e. 'wind', 'solar', 'other renewables', ...
    ember_mapper = {
        "other fossil": "unknown",
        "bioenergy": "biomass",
        "other renewables": "unknown",
    }

    if isinstance(row[category_col], str):
        mode = row[category_col].lower()
        if mode in ENERGIES:
            production_mode = mode
        elif (
            row["zone_key"] in SPECIFIC_MODE_MAPPING
            and mode in SPECIFIC_MODE_MAPPING[row["zone_key"]]
        ):
            production_mode = SPECIFIC_MODE_MAPPING[row["zone_key"]][mode]
        elif mode in ember_mapper:
            production_mode = ember_mapper[mode]
        else:
            production_mode = "unknown"
            logger.info(
                f"Unknown production mode: {row[category_col]}. Defaulting to unknown"
            )

    return production_mode


def format_ember_data(ember_df: pd.DataFrame) -> pd.DataFrame:
    ember_df.query(
        'variable != "Clean" and variable != "Fossil" and variable != "Wind and solar"',
        inplace=True,
    )
    ember_df["country_code_iso2"] = ember_df["country_code"].apply(
        lambda x: pycountry.countries.get(alpha_3=x).alpha_2
        if pycountry.countries.get(alpha_3=x)
        else None
    )
    # Drop rows where country code conversion failed
    ember_df.dropna(subset=["country_code_iso2"], inplace=True)
    ember_df = ember_df.loc[ember_df["country_code_iso2"].isin(EMBER_ZONES)]

    df_capacity = ember_df[["country_code_iso2", "year", "variable", "capacity_gw"]]
    df_capacity = df_capacity.rename(
        columns={
            "country_code_iso2": "zone_key",
            "variable": "mode",
        }
    )
    df_capacity["datetime"] = df_capacity["year"].apply(lambda x: datetime(x, 1, 1))
    df_capacity["capacity_mw"] = pd.to_numeric(
        df_capacity["capacity_gw"] * 1000, errors="coerce"
    ).astype(float)  # convert from GW to MW
    df_capacity.drop(columns=["capacity_gw"], inplace=True)
    df_capacity.dropna(subset=["capacity_mw"], inplace=True)

    df_capacity["mode"] = df_capacity.apply(_ember_production_mode_mapper, axis=1)
    df_capacity = (
        df_capacity.groupby(["zone_key", "datetime", "mode"])[["capacity_mw"]]
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
            mode_capacity["value"] = round(float(data["capacity_mw"]), 0)
            mode_capacity["source"] = SOURCE
            zone_capacity[data["mode"]] = mode_capacity
        all_capacity[zone] = zone_capacity
    return all_capacity


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session, zone_key: ZoneKey | None = None
) -> dict[str, Any]:
    df_capacity = get_ember_yearly_data(
        country_iso2=zone_key, year=target_datetime.year
    )
    df_capacity = format_ember_data(df_capacity)
    all_capacity = get_capacity_dict_from_df(df_capacity)
    logger.info(f"Fetched capacity data from Ember for {target_datetime.year}")
    return all_capacity


def fetch_production_capacity(
    target_datetime: datetime, zone_key: ZoneKey, session: Session
) -> dict[str, Any] | None:
    all_capacity = fetch_production_capacity_for_all_zones(
        target_datetime=target_datetime, session=session, zone_key=zone_key
    )
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
