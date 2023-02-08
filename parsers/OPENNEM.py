from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Dict, List, Mapping, Optional, Tuple, Union

import arrow
import pandas as pd
import requests
from requests import Session

from parsers.lib.config import refetch_frequency

REFETCH_FREQUENCY = timedelta(days=21)


ZONE_KEY_TO_REGION = {
    "AU-NSW": "NSW1",
    "AU-QLD": "QLD1",
    "AU-SA": "SA1",
    "AU-TAS": "TAS1",
    "AU-VIC": "VIC1",
    "AU-WA": "WEM",
}
ZONE_KEY_TO_NETWORK = {
    "AU-NSW": "NEM",
    "AU-QLD": "NEM",
    "AU-SA": "NEM",
    "AU-TAS": "NEM",
    "AU-VIC": "NEM",
    "AU-WA": "WEM",
}
EXCHANGE_MAPPING_DICTIONARY = {
    "AU-NSW->AU-QLD": {
        "region_id": "NSW1->QLD1",
        "direction": 1,
    },
    "AU-NSW->AU-VIC": {
        "region_id": "NSW1->VIC1",
        "direction": 1,
    },
    "AU-SA->AU-VIC": {
        "region_id": "SA1->VIC1",
        "direction": 1,
    },
    "AU-TAS->AU-VIC": {
        "region_id": "TAS1->VIC1",
        "direction": 1,
    },
}
OPENNEM_PRODUCTION_CATEGORIES = {
    "coal": ["COAL_BLACK", "COAL_BROWN"],
    "gas": ["GAS_CCGT", "GAS_OCGT", "GAS_RECIP", "GAS_STEAM"],
    "oil": ["DISTILLATE"],
    "hydro": ["HYDRO"],
    "wind": ["WIND"],
    "biomass": ["BIOENERGY_BIOGAS", "BIOENERGY_BIOMASS"],
    "solar": ["SOLAR_UTILITY", "SOLAR_ROOFTOP"],
}
OPENNEM_STORAGE_CATEGORIES = {
    # Storage
    "battery": ["BATTERY_DISCHARGING", "BATTERY_CHARGING"],
    "hydro": ["PUMPS"],
}
SOURCE = "opennem.org.au"


def dataset_to_df(dataset):
    series = dataset["history"]
    interval = series["interval"]
    dt_start = arrow.get(series["start"]).datetime
    dt_end = arrow.get(series["last"]).datetime
    data_type = dataset["data_type"]
    _id = dataset.get("id")

    if data_type != "power":
        name = data_type.upper()
    else:
        # When `power` is given, the multiple power sources will be given
        # we therefore set `name` to the power source
        name = _id.split(".")[-2].upper()

    # Turn into minutes
    if interval[-1] == "m":
        interval += "in"

    index = pd.date_range(start=dt_start, end=dt_end, freq=interval)
    assert len(index) == len(series["data"])
    df = pd.DataFrame(index=index, data=series["data"], columns=[name])

    return df


def process_solar_rooftop(df: pd.DataFrame) -> pd.DataFrame:
    if "SOLAR_ROOFTOP" in df:
        # at present, solar rooftop data comes in each 30 mins.
        # Resample data to not require interpolation
        return df.resample("30T").mean()
    return df


def get_capacities(filtered_datasets: List[Mapping], region: str) -> pd.Series:
    # Parse capacity data
    capacities = dict(
        [
            (obj["id"].split(".")[-2].upper(), obj.get("x_capacity_at_present"))
            for obj in filtered_datasets
            if obj["region"] == region
        ]
    )
    return pd.Series(capacities)


def sum_vector(pd_series, keys, ignore_nans=False):
    # Only consider keys that are in the pd_series
    filtered_keys = pd_series.index.intersection(keys)

    # Require all present keys to be non-null
    pd_series_filtered = pd_series.loc[filtered_keys]
    nan_filter = pd_series_filtered.notnull().all() | ignore_nans
    if filtered_keys.size and nan_filter:
        return pd_series_filtered.fillna(0).sum()
    else:
        return None


def filter_production_objs(
    objs: List[Dict], logger: Logger = getLogger(__name__)
) -> List[Dict]:
    def filter_solar_production(obj: Dict) -> bool:
        if (
            "solar" in obj.get("production", {})
            and obj["production"]["solar"] is not None
        ):
            return True
        return False

    all_filters = [filter_solar_production]

    filtered_objs = []
    for obj in objs:
        _valid = True
        for f in all_filters:
            _valid &= f(obj)
        if _valid:
            filtered_objs.append(obj)
        else:
            logger.warning(
                f"Entry for {obj['datetime']} is dropped because it does not pass the production filter."
            )

    return filtered_objs


def generate_url(
    zone_key: str, is_flow, target_datetime: datetime, logger: Logger
) -> str:
    if target_datetime:
        network = ZONE_KEY_TO_NETWORK[zone_key]
        # We will fetch since the beginning of the current month
        month = arrow.get(target_datetime).floor("month").format("YYYY-MM-DD")
        if is_flow:
            url = (
                f"http://api.opennem.org.au/stats/flow/network/{network}?month={month}"
            )
        else:
            region = ZONE_KEY_TO_REGION.get(zone_key)
            url = f"http://api.opennem.org.au/stats/power/network/fueltech/{network}/{region}?month={month}"
    else:
        # Contains flows and production combined
        url = f"https://data.opennem.org.au/v3/clients/em/latest.json"

    return url


def fetch_main_price_df(
    zone_key: Union[str, None] = None,
    sorted_zone_keys: Union[str, None] = None,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    return _fetch_main_df(
        "price",
        zone_key=zone_key,
        sorted_zone_keys=sorted_zone_keys,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )[0]


def fetch_main_power_df(
    zone_key: Union[str, None] = None,
    sorted_zone_keys: Union[str, None] = None,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Tuple[pd.DataFrame, list]:
    df, filtered_datasets = _fetch_main_df(
        "power",
        zone_key=zone_key,
        sorted_zone_keys=sorted_zone_keys,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # Solar rooftop is a special case
    df = process_solar_rooftop(df)
    return df, filtered_datasets


def _fetch_main_df(
    data_type,
    zone_key: str,
    sorted_zone_keys: str,
    session: Session,
    target_datetime: datetime,
    logger: Logger,
) -> Tuple[pd.DataFrame, list]:
    region = ZONE_KEY_TO_REGION.get(zone_key)
    url = generate_url(
        zone_key=zone_key or sorted_zone_keys[0],
        is_flow=sorted_zone_keys is not None,
        target_datetime=target_datetime,
        logger=logger,
    )

    # Fetches the last week of data
    logger.info(f"Requesting {url}..")
    r = (session or requests).get(url)
    r.raise_for_status()
    logger.debug("Parsing JSON..")
    datasets = r.json()["data"]
    logger.debug("Filtering datasets..")

    def filter_dataset(ds: dict) -> bool:
        filter_data_type = ds["type"] == data_type
        filter_region = False
        if zone_key:
            filter_region |= ds.get("region") == region
        if sorted_zone_keys:
            filter_region |= (
                ds.get("id").split(".")[-2]
                == EXCHANGE_MAPPING_DICTIONARY["->".join(sorted_zone_keys)]["region_id"]
            )
        return filter_data_type and filter_region

    filtered_datasets = [ds for ds in datasets if filter_dataset(ds)]
    logger.debug("Concatenating datasets..")
    df = pd.concat([dataset_to_df(ds) for ds in filtered_datasets], axis=1)

    # Sometimes we get twice the columns. In that case, only return the first one
    is_duplicated_column = df.columns.duplicated(keep="last")
    if is_duplicated_column.sum():
        logger.warning(
            f"Dropping columns {df.columns[is_duplicated_column]} that appear more than once"
        )
        df = df.loc[:, is_duplicated_column]

    return df, filtered_datasets


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_production(
    zone_key: Union[str, None] = None,
    session: Optional[Session] = None,
    target_datetime: Optional[Session] = None,
    logger: Logger = getLogger(__name__),
):
    df, filtered_datasets = fetch_main_power_df(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    region = ZONE_KEY_TO_REGION.get(zone_key)
    if region:
        capacities = get_capacities(filtered_datasets, region)
    else:
        capacities = pd.Series()

    # Drop interconnectors
    df = df.drop([x for x in df.columns if "->" in x], axis=1)

    # Make sure charging is counted positively
    # and discharging negetively
    if "BATTERY_DISCHARGING" in df.columns:
        df["BATTERY_DISCHARGING"] = df["BATTERY_DISCHARGING"] * -1

    logger.debug("Preparing final objects..")
    objs = [
        {
            "datetime": arrow.get(dt.to_pydatetime()).datetime,
            "production": {  # Unit is MW
                "coal": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["coal"]),
                "gas": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["gas"]),
                "oil": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["oil"]),
                "hydro": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["hydro"]),
                "wind": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["wind"]),
                "biomass": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["biomass"]),
                # We here assume all rooftop solar is fed to the grid
                # This assumption should be checked and we should here only report
                # grid-level generation
                "solar": sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES["solar"]),
            },
            "storage": {
                # opennem reports charging as negative, we here should report as positive
                # Note: we made the sign switch before, so we can just sum them up
                "battery": sum_vector(row, OPENNEM_STORAGE_CATEGORIES["battery"]),
                # opennem reports pumping as positive, we here should report as positive
                "hydro": sum_vector(row, OPENNEM_STORAGE_CATEGORIES["hydro"]),
            },
            "capacity": {
                "coal": sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES["coal"]),
                "gas": sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES["gas"]),
                "oil": sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES["oil"]),
                "hydro": sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES["hydro"]),
                "wind": sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES["wind"]),
                "biomass": sum_vector(
                    capacities, OPENNEM_PRODUCTION_CATEGORIES["biomass"]
                ),
                "solar": sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES["solar"]),
                "hydro storage": capacities.get(OPENNEM_STORAGE_CATEGORIES["hydro"][0]),
                "battery storage": capacities.get(
                    OPENNEM_STORAGE_CATEGORIES["battery"][0]
                ),
            },
            "source": SOURCE,
            "zoneKey": zone_key,
        }
        for dt, row in df.iterrows()
    ]

    objs = filter_production_objs(objs)

    # Validation
    logger.debug("Validating..")
    for obj in objs:
        for k, v in obj["production"].items():
            if v is None:
                continue
            if v < 0 and v > -50:
                # Set small negative values to 0
                logger.warning(
                    f"Setting small value of {k} ({v}) to 0.", extra={"key": zone_key}
                )
                obj["production"][k] = 0

    return objs


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_price(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    df = fetch_main_price_df(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    df = df.loc[~df["PRICE"].isna()]  # Only keep prices that are defined
    return [
        {
            "datetime": arrow.get(dt.to_pydatetime()).datetime,
            "price": sum_vector(row, ["PRICE"]),  # currency / MWh
            "currency": "AUD",
            "source": SOURCE,
            "zoneKey": zone_key,
        }
        for dt, row in df.iterrows()
    ]


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[Session] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    key = "->".join(sorted_zone_keys)
    df, _ = fetch_main_power_df(
        sorted_zone_keys=sorted_zone_keys,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    direction = EXCHANGE_MAPPING_DICTIONARY[key]["direction"]

    # Take the first column (there's only one)
    series = df.iloc[:, 0]

    return [
        {
            "datetime": arrow.get(dt.to_pydatetime()).datetime,
            "netFlow": value * direction,
            "source": SOURCE,
            "sortedZoneKeys": key,
        }
        for dt, value in series.iteritems()
    ]


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""
    # print(fetch_price('AU-SA'))
    # print(fetch_production('AU-WA'))
    # print(fetch_production('AU-SA', target_datetime=arrow.get('2020-01-01T00:00:00Z').datetime))
    # print(
    #     fetch_production(
    #         "AU-SA", target_datetime=arrow.get("2020-01-01T00:00:00Z").datetime
    #     )
    # )
    print(fetch_production("AU-NSW"))
