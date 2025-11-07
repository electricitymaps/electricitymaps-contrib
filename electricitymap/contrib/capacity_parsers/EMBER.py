import logging
from datetime import datetime
from time import sleep
from typing import Any

import pandas as pd
import pycountry
import requests
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.contrib.config.constants import ENERGIES
from electricitymap.contrib.parsers.lib.utils import get_token

""" Collects capacity data from the yearly electricity data from Ember. The data and documentation can be found here: https://ember-climate.org/data-catalogue/yearly-electricity-data/"""
logger = logging.getLogger(__name__)
EMBER_URL = "https://ember-climate.org"
SOURCE = "Ember, Yearly electricity data"
START_YEAR = 2017
SPECIFIC_MODE_MAPPING = {
    "AR": {"other fossil": "unknown"},
    "BD": {"other fossil": "oil"},
    "BO": {"other fossil": "oil"},
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


def get_ember_capacity_yearly_data(country_iso2: ZoneKey, session: Session) -> str:
    """
    Creates a URL to fetch generation_yearly data from the API,
    using ISO 3 country code and a year
    ex: 'https://api.ember-energy.org/data-tools/electricity-capacity/yearly?entity=xxx&api_key=xxxx
    Args:
        country_iso2 (str | None): ISO 2 country code (e.g., "FR").
        session (Session): The requests session to use.
    Returns:
        pd.DataFrame: A dataframe with the capacity data.
    """
    ember_api_key = get_token("EMBER_CAPACITY_KEY")
    if not ember_api_key:
        raise ValueError("EMBER_CAPACITY_KEY not found in environment variables")

    # Go from ISO2 to country name, capitalize each word

    if country_iso2 in SPECIAL_MAPPING_ZONE_KEY:
        country_name = SPECIAL_MAPPING_ZONE_KEY[country_iso2]
    else:
        country = pycountry.countries.get(alpha_2=country_iso2)
        if country:
            country_name = country.name.title()
        else:
            raise ValueError(f"Invalid ISO2 country code: {country_iso2}")

    query_params = {
        "entity": country_name,
        "api_key": ember_api_key,
    }

    base_url = "https://api.ember-energy.org/data-tools/electricity-capacity/yearly"

    # Retry up to 3 times with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Fetching Ember capacity data for {country_iso2} (attempt {attempt + 1}/{max_retries})"
            )
            response = session.get(base_url, params=query_params, timeout=30)
            response.raise_for_status()

            # Add a small delay to avoid spamming the API
            sleep(1)

            df_raw = pd.DataFrame(response.json()["data"])
            df_raw["country_code_iso2"] = country_iso2
            return df_raw

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(
                    f"Failed to fetch Ember data for {country_iso2}: {e}. Retrying in {wait_time}s..."
                )
                sleep(wait_time)
            else:
                logger.error(
                    f"Failed to fetch Ember data for {country_iso2} after {max_retries} attempts: {e}"
                )
                raise

    # This should never be reached as the loop always returns or raises
    raise RuntimeError(
        f"Failed to fetch Ember data for {country_iso2}: retry loop completed without returning"
    )


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
        if (
            row["zone_key"] in SPECIFIC_MODE_MAPPING
            and mode in SPECIFIC_MODE_MAPPING[row["zone_key"]]
        ):
            production_mode = SPECIFIC_MODE_MAPPING[row["zone_key"]][mode]
        elif mode in ENERGIES:
            production_mode = mode
        elif mode in ember_mapper:
            production_mode = ember_mapper[mode]
        else:
            production_mode = "unknown"
            raise ValueError(f"Unknown production mode: {row[category_col]}")

    return production_mode


def transform_ember_data(ember_df: pd.DataFrame) -> pd.DataFrame:
    if ember_df.empty is True:
        logger.warning("Empty Ember data received")
        raise ValueError("Empty Ember data received")
    df = ember_df.loc[~ember_df["is_aggregate_series"]].reset_index(drop=True)

    df_capacity = df[["country_code_iso2", "date", "series", "capacity_gw"]].rename(
        columns={"date": "year", "series": "variable"}
    )

    df_capacity = df_capacity.rename(
        columns={
            "country_code_iso2": "zone_key",
            "variable": "mode",
        }
    )
    df_capacity["datetime"] = df_capacity["year"].apply(
        lambda x: datetime(int(x), 1, 1)
    )
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


def get_capacity_dict_from_df(
    df_capacity: pd.DataFrame, zone_key: ZoneKey, target_datetime: datetime
) -> dict[str, Any]:
    """Get capacity data for a specific zone for a specific year. The unit is the MW

    Args:
        df_capacity: DataFrame with capacity data
        zone_key: The zone key
        target_datetime: The target datetime (year will be used to filter data)

    Returns:
        Dictionary with capacity data per mode for the target year
    """
    if [zone_key] != df_capacity.index.unique().tolist():
        raise ValueError(f"Zone key {zone_key} not found in dataframe")

    # Filter data for the target year
    target_year = target_datetime.year
    df_year = df_capacity[df_capacity["datetime"].dt.year == target_year]

    if df_year.empty:
        logger.warning(f"No capacity data for {zone_key} in year {target_year}")
        return {}

    zone_capacity = {}
    for _i, data in df_year.iterrows():
        mode_capacity = {}
        mode_capacity["datetime"] = data["datetime"].strftime("%Y-%m-%d")
        mode_capacity["source"] = SOURCE
        mode_capacity["value"] = round(float(data["capacity_mw"]), 2)

        # Store single dict per mode (not a list)
        zone_capacity[data["mode"]] = mode_capacity

    return zone_capacity


def remove_consecutive_duplicates(
    capacity_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove consecutive entries with the same value, keeping only the first occurrence.

    This optimizes the capacity data by removing redundant year-over-year entries
    where the capacity hasn't changed.

    Args:
        capacity_list: List of capacity entries sorted by datetime

    Returns:
        Optimized list with consecutive duplicates removed
    """
    if not capacity_list:
        return []

    # Sort by datetime to ensure chronological order
    sorted_list = sorted(capacity_list, key=lambda x: x["datetime"])

    # Always keep the first entry
    optimized = [sorted_list[0]]

    # Only add entries where the value changed from the previous entry
    for entry in sorted_list[1:]:
        if entry["value"] != optimized[-1]["value"]:
            optimized.append(entry)

    return optimized


def get_capacity_dict_all_years_from_df(
    df_capacity: pd.DataFrame, zone_key: ZoneKey
) -> dict[str, Any]:
    """Get capacity data for a specific zone for ALL available years. The unit is the MW

    Args:
        df_capacity: DataFrame with capacity data
        zone_key: The zone key

    Returns:
        Dictionary with capacity data per mode as lists (all years)
    """
    if [zone_key] != df_capacity.index.unique().tolist():
        raise ValueError(f"Zone key {zone_key} not found in dataframe")

    zone_capacity = {}
    for _i, data in df_capacity.iterrows():
        mode_capacity = {}
        mode_capacity["datetime"] = data["datetime"].strftime("%Y-%m-%d")
        mode_capacity["source"] = SOURCE
        mode_capacity["value"] = round(float(data["capacity_mw"]), 2)

        # Initialize list for this mode if it doesn't exist
        if data["mode"] not in zone_capacity:
            zone_capacity[data["mode"]] = []

        # Append the entry to the list for this mode
        zone_capacity[data["mode"]].append(mode_capacity)

    # Remove consecutive duplicates for each mode
    for mode in zone_capacity:
        zone_capacity[mode] = remove_consecutive_duplicates(zone_capacity[mode])

    return zone_capacity


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    """Get capacity data for a specific zone for a specific year. The unit is the MW

    Args:
        zone_key: The zone key (ISO2 country code)
        target_datetime: The target datetime (year will be used to filter data)
        session: The requests session

    Returns:
        Dictionary with capacity data for the zone
    """
    session = session or Session()
    df_capacity = get_ember_capacity_yearly_data(
        country_iso2=zone_key,
        session=session,
    )
    df_capacity = transform_ember_data(df_capacity)
    capacity = get_capacity_dict_from_df(df_capacity, zone_key, target_datetime)

    if capacity:
        logger.info(
            f"Fetched capacity for {zone_key} in {target_datetime.year}: \n{capacity}"
        )
    return capacity if capacity else None


def fetch_production_capacity_all_years(
    zone_key: ZoneKey, session: Session | None = None
) -> dict[str, Any]:
    """Get capacity data for a specific zone for ALL available years >= 2017. The unit is the MW

    This function fetches all years available from EMBER in one API call and returns
    them in the list format that matches the zone YAML configuration structure.

    Data is filtered to start from 2017 and consecutive duplicate values are
    automatically removed to optimize the data.

    Args:
        zone_key: The zone key (ISO2 country code)
        session: The requests session

    Returns:
        Dictionary with capacity data per mode as lists containing all years >= 2017
        (with consecutive duplicates removed):
        {
            "coal": [
                {"datetime": "2017-01-01", "value": 1234.56, "source": "..."},
                {"datetime": "2022-01-01", "value": 1245.67, "source": "..."}  # 2018-2021 removed (duplicates)
            ],
            "solar": [...]
        }
    """
    session = session or Session()
    df_capacity = get_ember_capacity_yearly_data(
        country_iso2=zone_key,
        session=session,
    )
    df_capacity = transform_ember_data(df_capacity)
    # Filter to only include years >= 2017
    df_capacity = df_capacity[df_capacity["datetime"].dt.year >= START_YEAR]
    capacity = get_capacity_dict_all_years_from_df(df_capacity, zone_key)

    if capacity:
        years = set()
        for mode_data in capacity.values():
            for entry in mode_data:
                years.add(entry["datetime"][:4])
        logger.info(
            f"Fetched capacity for {zone_key} for years {sorted(years)}: {len(capacity)} modes"
        )
    return capacity


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session | None = None
) -> dict[str, Any]:
    """Get capacity data for all zones supported by Ember for a specific year.

    Args:
        target_datetime: The target datetime (year will be used to filter data)
        session: The requests session

    Returns:
        Dictionary with capacity data for all zones: {zone_key: {mode: dict}}
    """
    session = session or Session()
    all_capacity = {}

    for zone_key in EMBER_ZONES:
        try:
            capacity = fetch_production_capacity(zone_key, target_datetime, session)
            if capacity:
                all_capacity[zone_key] = capacity
        except Exception as e:
            logger.error(f"Failed to fetch capacity for {zone_key}: {e}")
            continue

    return all_capacity


def fetch_production_capacity_for_all_zones_all_years(
    session: Session | None = None,
) -> dict[str, Any]:
    """Get capacity data for ALL zones for ALL available years.

    This function is useful for doing a complete update of all EMBER zones at once.

    Args:
        session: The requests session

    Returns:
        Dictionary with capacity data for all zones with all years:
        {
            "FR": {
                "coal": [{"datetime": "2021-01-01", "value": 1234, "source": "..."}],
                "solar": [...]
            },
            "DE": {...}
        }
    """
    session = session or Session()
    all_capacity = {}

    logger.info(f"Fetching capacity for {len(EMBER_ZONES)} zones...")
    for zone_key in EMBER_ZONES:
        try:
            capacity = fetch_production_capacity_all_years(zone_key, session)
            if capacity:
                all_capacity[zone_key] = capacity
        except Exception as e:
            logger.error(f"Failed to fetch capacity for {zone_key}: {e}")
            continue

    return all_capacity


SPECIAL_MAPPING_ZONE_KEY = {
    "FK": "Falkland Islands [Malvinas]",
    "KP": "North Korea",
    "KR": "South Korea",
    "LA": "Lao",
    "MO": "Macao (SAR of China)",
    "PS": "Palestine (State of)",
    "RU": "Russia",
    "SY": "Syria",
    "TR": "Türkiye",
    "TW": "Taiwan (China)",
    "TZ": "Tanzania (the United Republic of)",
    "VI": "Virgin Islands (U.S.)",
}
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    session = Session()

    # Example 1: Fetch capacity for one year (for use with update_capacity_configuration.py)
    print("\n=== Example 1: Single year ===")
    FR_single_year = fetch_production_capacity(
        zone_key="FR", target_datetime=datetime(2024, 1, 1), session=session
    )
    print(f"FR capacity data for 2024: {list(FR_single_year.keys())}")

    # Example 2: Fetch capacity for all years at once
    print("\n=== Example 2: All years for one zone ===")
    FR_all_years = fetch_production_capacity_all_years(zone_key="FR", session=session)
    print("FR capacity data for all years:")
    for mode, data in FR_all_years.items():
        print(f"  {mode}: {len(data)} years")

    # Example 3: Fetch capacity for all zones and all years (use with caution - many API calls!)
    # Uncomment to run:
    # print("\n=== Example 3: All zones, all years ===")
    # all_data = fetch_production_capacity_for_all_zones_all_years(session=session)
    # print(f"Fetched data for {len(all_data)} zones")
