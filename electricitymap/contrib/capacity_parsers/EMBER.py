import io
import logging
from datetime import datetime
from time import sleep
from typing import Any

import pandas as pd
import pycountry
import requests
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.contrib.config.constants import ENERGIES
from electricitymap.contrib.parsers.lib.utils import get_token

""" Collects installed capacity from two Ember datasets:
- Wind and solar from the monthly capacity API.
  API docs: https://api.ember-energy.org/v1/docs#/Main%20routes/getMonthlyCapacity
  Dataset: https://ember-energy.org/data/monthly-wind-and-solar-capacity-data/
- All other modes from the yearly electricity data CSV, as the API only covers wind and solar.
  Dataset: https://ember-energy.org/data/yearly-electricity-data/

If the monthly API has no data for a mode (e.g. a country it does not cover),
the yearly value is used instead."""
logger = logging.getLogger(__name__)
EMBER_URL = "https://ember-climate.org"
EMBER_CAPACITY_URL = "https://api.ember-energy.org/v1/installed-capacity/monthly"
EMBER_YEARLY_CSV_URL = "https://storage.googleapis.com/emb-prod-bkt-publicdata/public-downloads/yearly_full_release_long_format.csv"
SOURCE_MONTHLY = "Ember, Monthly wind and solar capacity data"
SOURCE_YEARLY = "Ember, Yearly electricity data"
START_YEAR = 2017
# 'Wind' is Ember's aggregate of onshore and offshore wind, so only it is requested
EMBER_SERIES = ["Solar", "Wind"]
EMBER_MODE_MAPPING = {
    "other fossil": "unknown",
    "bioenergy": "biomass",
    "other renewables": "unknown",
}
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
    "NI": {"other fossil": "oil", "other renewables": "geothermal"},
    "NZ": {"other renewables": "geothermal"},
    "SG": {"other fossil": "coal"},
    "SV": {"other renewables": "geothermal"},
    "TR": {"other fossil": "oil", "other renewables": "geothermal"},
    "TW": {"other fossil": "oil"},
    "UY": {"other fossil": "unknown"},
    "ZA": {"other fossil": "oil"},
}
CAPACITY_COLUMNS = ["zone_key", "datetime", "mode", "source", "capacity_mw"]

EMBER_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["EMBER"]

# The yearly CSV covers all countries, so it is downloaded once and reused per zone
_yearly_capacity_cache: pd.DataFrame | None = None


def _to_iso3(country_iso2: ZoneKey) -> str:
    country = pycountry.countries.get(alpha_2=country_iso2)
    if country is None:
        raise ValueError(f"Invalid ISO2 country code: {country_iso2}")
    return country.alpha_3


def _get_with_retries(
    session: Session, url: str, description: str, **kwargs: Any
) -> Response:
    # Retry up to 3 times with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {description} (attempt {attempt + 1}/{max_retries})")
            response = session.get(url, **kwargs)
            response.raise_for_status()

            # Add a small delay to avoid spamming the API
            sleep(1)
            return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(
                    f"Failed to fetch {description}: {e}. Retrying in {wait_time}s..."
                )
                sleep(wait_time)
            else:
                logger.error(
                    f"Failed to fetch {description} after {max_retries} attempts: {e}"
                )
                raise

    # This should never be reached as the loop always returns or raises
    raise RuntimeError(
        f"Failed to fetch {description}: retry loop completed without returning"
    )


def get_ember_capacity_monthly_data(
    country_iso2: ZoneKey, session: Session
) -> pd.DataFrame:
    """
    Fetches monthly installed wind and solar capacity from the Ember API for one country.
    The API expects an ISO 3 country code, so the ISO 2 zone key is converted first
    (e.g., "FR" -> "FRA").
    ex: 'https://api.ember-energy.org/v1/installed-capacity/monthly?entity_code=FRA&series=Solar,Wind&start_date=2017-01&api_key=xxxx'
    Args:
        country_iso2 (str): ISO 2 zone key (e.g., "FR"), converted to ISO 3 for the API.
        session (Session): The requests session to use.
    Returns:
        pd.DataFrame: A dataframe with the capacity data.
    """
    ember_api_key = get_token("EMBER_CAPACITY_KEY")
    if not ember_api_key:
        raise ValueError("EMBER_CAPACITY_KEY not found in environment variables")

    query_params = {
        "entity_code": _to_iso3(country_iso2),
        "series": ",".join(EMBER_SERIES),
        "start_date": f"{START_YEAR}-01",
        "api_key": ember_api_key,
    }
    response = _get_with_retries(
        session,
        EMBER_CAPACITY_URL,
        f"Ember monthly capacity data for {country_iso2}",
        params=query_params,
        timeout=30,
    )
    df_raw = pd.DataFrame(response.json()["data"])
    df_raw["country_code_iso2"] = country_iso2
    return df_raw


def get_ember_capacity_yearly_data(session: Session) -> pd.DataFrame:
    """
    Downloads Ember's yearly electricity data CSV and returns the capacity rows
    per fuel for all countries. The download is cached for the lifetime of the process.
    Args:
        session (Session): The requests session to use.
    Returns:
        pd.DataFrame: A dataframe with the capacity data for all countries.
    """
    global _yearly_capacity_cache
    if _yearly_capacity_cache is None:
        response = _get_with_retries(
            session, EMBER_YEARLY_CSV_URL, "Ember yearly electricity data", timeout=300
        )
        df = pd.read_csv(
            io.BytesIO(response.content),
            usecols=[
                "ISO 3 code",
                "Year",
                "Category",
                "Subcategory",
                "Variable",
                "Value",
            ],
        )
        _yearly_capacity_cache = df.loc[
            (df["Category"] == "Capacity") & (df["Subcategory"] == "Fuel")
        ].reset_index(drop=True)
    return _yearly_capacity_cache


def _ember_production_mode_mapper(zone_key: ZoneKey, series: str) -> str:
    mode = series.lower()
    zone_mapping = SPECIFIC_MODE_MAPPING.get(zone_key, {})
    if mode in zone_mapping:
        return zone_mapping[mode]
    if mode in ENERGIES:
        return mode
    if mode in EMBER_MODE_MAPPING:
        return EMBER_MODE_MAPPING[mode]
    raise ValueError(f"Unknown production mode: {series}")


def _format_capacity_df(df_capacity: pd.DataFrame) -> pd.DataFrame:
    """Converts GW to MW, maps Ember series to modes and sums series mapped to the same mode.
    Expects the columns zone_key, datetime, mode (the Ember series), source and capacity_gw.
    """
    df_capacity = df_capacity.copy()
    df_capacity["capacity_mw"] = (
        pd.to_numeric(df_capacity["capacity_gw"], errors="coerce").astype(float) * 1000
    )  # convert from GW to MW
    df_capacity = df_capacity.dropna(subset=["capacity_mw"])
    if df_capacity.empty:
        return pd.DataFrame(columns=CAPACITY_COLUMNS).set_index("zone_key")

    df_capacity["mode"] = [
        _ember_production_mode_mapper(zone_key, series)
        for zone_key, series in zip(
            df_capacity["zone_key"], df_capacity["mode"], strict=True
        )
    ]
    return (
        df_capacity.groupby(["zone_key", "datetime", "mode", "source"])[["capacity_mw"]]
        .sum()
        .reset_index()
        .set_index(["zone_key"])
    )


def transform_ember_monthly_data(ember_df: pd.DataFrame) -> pd.DataFrame:
    if ember_df.empty or "series" not in ember_df.columns:
        logger.warning("Empty Ember monthly data received")
        return pd.DataFrame(columns=CAPACITY_COLUMNS).set_index("zone_key")
    # Guard against series we did not request, e.g. 'Onshore wind' which is part of 'Wind'
    df = ember_df.loc[ember_df["series"].isin(EMBER_SERIES)]

    df_capacity = pd.DataFrame(
        {
            "zone_key": df["country_code_iso2"],
            # Dates are monthly (YYYY-MM), parsed to the first day of the month in UTC
            "datetime": pd.to_datetime(df["date"], utc=True),
            "mode": df["series"],
            "source": SOURCE_MONTHLY,
            "capacity_gw": df["capacity_gw"],
        }
    )
    return _format_capacity_df(df_capacity)


def transform_ember_yearly_data(
    ember_df: pd.DataFrame, zone_key: ZoneKey
) -> pd.DataFrame:
    df = ember_df.loc[ember_df["ISO 3 code"] == _to_iso3(zone_key)]
    if df.empty:
        logger.warning(f"No Ember yearly data for {zone_key}")

    df_capacity = pd.DataFrame(
        {
            "zone_key": zone_key,
            # Yearly values are dated to the first day of the year in UTC
            "datetime": pd.to_datetime(df["Year"].astype(str), format="%Y", utc=True),
            "mode": df["Variable"],
            "source": SOURCE_YEARLY,
            "capacity_gw": df["Value"],
        }
    )
    return _format_capacity_df(df_capacity)


def get_ember_capacity_data(zone_key: ZoneKey, session: Session) -> pd.DataFrame:
    """Combines monthly wind and solar capacity with yearly capacity for all other modes.
    Modes present in the monthly data are dropped from the yearly data, so each mode
    comes from a single source.
    """
    df_monthly = transform_ember_monthly_data(
        get_ember_capacity_monthly_data(country_iso2=zone_key, session=session)
    )
    df_yearly = transform_ember_yearly_data(
        get_ember_capacity_yearly_data(session=session), zone_key
    )
    df_yearly = df_yearly.loc[~df_yearly["mode"].isin(df_monthly["mode"].unique())]

    non_empty = [df for df in (df_yearly, df_monthly) if not df.empty]
    if not non_empty:
        raise ValueError(f"No Ember capacity data for {zone_key}")
    return pd.concat(non_empty)


def get_capacity_dict_from_df(
    df_capacity: pd.DataFrame, zone_key: ZoneKey, target_datetime: datetime
) -> dict[str, Any]:
    """Get capacity data for a specific zone for a specific date. The unit is the MW

    Monthly data (wind and solar) is matched on the year and month of target_datetime,
    yearly data (all other modes) on the year only.

    Args:
        df_capacity: DataFrame with capacity data
        zone_key: The zone key
        target_datetime: The target datetime

    Returns:
        Dictionary with capacity data per mode for the target date
    """
    if [zone_key] != df_capacity.index.unique().tolist():
        raise ValueError(f"Zone key {zone_key} not found in dataframe")

    is_yearly = df_capacity["source"] == SOURCE_YEARLY
    same_year = df_capacity["datetime"].dt.year == target_datetime.year
    same_month = df_capacity["datetime"].dt.month == target_datetime.month
    df_target = df_capacity[same_year & (is_yearly | same_month)]

    if df_target.empty:
        logger.warning(f"No capacity data for {zone_key} in {target_datetime:%Y-%m}")
        return {}

    zone_capacity = {}
    for _i, data in df_target.iterrows():
        mode_capacity = {}
        mode_capacity["datetime"] = data["datetime"].strftime("%Y-%m-%d")
        mode_capacity["source"] = data["source"]
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
        mode_capacity["source"] = data["source"]
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
    """Get capacity data for a specific zone for a specific date. The unit is the MW

    Args:
        zone_key: The zone key (ISO2 country code)
        target_datetime: The target datetime (year and month for wind and solar, year for other modes)
        session: The requests session

    Returns:
        Dictionary with capacity data for the zone
    """
    session = session or Session()
    df_capacity = get_ember_capacity_data(zone_key, session)
    capacity = get_capacity_dict_from_df(df_capacity, zone_key, target_datetime)

    if capacity:
        logger.info(
            f"Fetched capacity for {zone_key} in {target_datetime:%Y-%m}: \n{capacity}"
        )
    return capacity if capacity else None


def fetch_production_capacity_all_years(
    zone_key: ZoneKey, session: Session | None = None
) -> dict[str, Any]:
    """Get capacity data for a specific zone for ALL available dates >= 2017. The unit is the MW

    Wind and solar come from the monthly API (one entry per month), all other modes
    from the yearly CSV (one entry per year). They are returned in the list format
    that matches the zone YAML configuration structure.

    Data is filtered to start from 2017 and consecutive duplicate values are
    automatically removed to optimize the data.

    Args:
        zone_key: The zone key (ISO2 country code)
        session: The requests session

    Returns:
        Dictionary with capacity data per mode as lists containing all dates >= 2017
        (with consecutive duplicates removed):
        {
            "wind": [
                {"datetime": "2017-01-01", "value": 1234.56, "source": "..."},
                {"datetime": "2017-06-01", "value": 1245.67, "source": "..."}  # Feb-May removed (duplicates)
            ],
            "gas": [
                {"datetime": "2017-01-01", "value": 2345.67, "source": "..."},
                {"datetime": "2021-01-01", "value": 2456.78, "source": "..."}  # 2018-2020 removed (duplicates)
            ],
        }
    """
    session = session or Session()
    df_capacity = get_ember_capacity_data(zone_key, session)
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    session = Session()

    # Example 1: Fetch capacity for one date (for use with update_capacity_configuration.py)
    print("\n=== Example 1: Single date ===")
    FR_single_year = fetch_production_capacity(
        zone_key="FR", target_datetime=datetime(2024, 1, 1), session=session
    )
    print(f"FR capacity data for 2024-01: {list(FR_single_year.keys())}")

    # Example 2: Fetch capacity for all years at once
    print("\n=== Example 2: All years for one zone ===")
    FR_all_years = fetch_production_capacity_all_years(zone_key="FR", session=session)
    print("FR capacity data for all years:")
    for mode, data in FR_all_years.items():
        print(f"  {mode}: {len(data)} data points")

    # Example 3: Fetch capacity for all zones and all years (use with caution - many API calls!)
    # Uncomment to run:
    # print("\n=== Example 3: All zones, all years ===")
    # all_data = fetch_production_capacity_for_all_zones_all_years(session=session)
    # print(f"Fetched data for {len(all_data)} zones")
