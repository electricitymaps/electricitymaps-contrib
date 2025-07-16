from datetime import datetime, timedelta
from logging import Logger, getLogger

import pandas as pd
import requests
from requests import Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

REFETCH_FREQUENCY = timedelta(days=7)


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

# exchanges are reconstructed from each zones total imports and exports
# all exchanges except AU-NSW->AU-VIC only have one connection so we can
# reconstruct the net flow by querying to leaf node
# see diagram below
#       QLD
#        |
#       NSW
#        |
#   SA--VIC
#        |
#       TAS
EXCHANGE_MAPPING_DICTIONARY = {
    "AU-NSW->AU-QLD": {
        "zone_to_query": "AU-QLD",
        "additional_zone_to_query": None,
        "direction": -1,
    },
    # we get this flow by substracting QLD imports/exports from NSW imports/exports
    "AU-NSW->AU-VIC": {
        "zone_to_query": "AU-NSW",
        "additional_zone_to_query": "AU-QLD",
        "direction": 1,
    },
    "AU-SA->AU-VIC": {
        "zone_to_query": "AU-SA",
        "additional_zone_to_query": None,
        "direction": 1,
    },
    "AU-TAS->AU-VIC": {
        "zone_to_query": "AU-TAS",
        "additional_zone_to_query": None,
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
    dt_start = datetime.fromisoformat(series["start"])
    dt_end = datetime.fromisoformat(series["last"])
    data_type = dataset["data_type"]
    _id = dataset.get("id")

    # When `power` is given, the multiple power sources will be given
    # we therefore set `name` to the power source
    name = data_type.upper() if data_type != "power" else _id.split(".")[-2].upper()

    # Turn into minutes
    if interval[-1] == "m":
        interval += "in"

    index = pd.date_range(start=dt_start, end=dt_end, freq=interval)
    # In some situation, some data points missing, the first dates are the ones to keep
    index = index[: len(series["data"])]
    df = pd.DataFrame(index=index, data=series["data"], columns=[name])
    if name == "SOLAR_ROOFTOP":
        breakpoint()

    return df


def sum_vector(pd_series, keys, ignore_nans=False) -> pd.Series | None:
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
    objs: list[dict], logger: Logger = getLogger(__name__)
) -> list[dict]:
    def filter_solar_production(obj: dict) -> bool:
        return bool(
            "solar" in obj.get("production", {})
            and obj["production"]["solar"] is not None
        )

    # The latest data points for AU-TAS are regularly containing only values for solar
    # and no other production values. This is likely an invalid report, so we filter it out.
    def only_solar_production(obj: dict) -> bool:
        return not (
            all(v is None for k, v in obj.get("production", {}).items() if k != "solar")
        )

    all_filters = [filter_solar_production, only_solar_production]

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


def generate_url(zone_key: str, target_datetime: datetime | None) -> str:
    # Only 7d or 30d data is available
    duration = (
        "7d"
        if not target_datetime
        or (datetime.now() - target_datetime.replace(tzinfo=None)) < timedelta(days=7)
        else "30d"
    )
    network = ZONE_KEY_TO_NETWORK[zone_key]
    region = ZONE_KEY_TO_REGION.get(zone_key)
    # Western Australia have no region in url
    region = "" if region == "WEM" else f"/{region}"
    url = f"https://data.openelectricity.org.au/v4/stats/au/{network}{region}/power/{duration}.json"

    return url


def fetch_main_price_df(
    zone_key: str | None = None,
    sorted_zone_keys: str | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    return _fetch_main_df(
        "price",
        zone_key=zone_key,
        sorted_zone_keys=sorted_zone_keys,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


def fetch_main_power_df(
    zone_key: str | None = None,
    additional_zone_key: str | None = None,
    direction: int | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> tuple[pd.DataFrame, list]:
    return _fetch_main_df(
        "power",
        zone_key=zone_key,
        additional_zone_key=additional_zone_key,
        direction=direction,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


def _fetch_main_df(
    data_type,
    zone_key: str,
    additional_zone_key: str | None = None,
    direction: int | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger | None = None,
) -> tuple[pd.DataFrame, list]:
    region = ZONE_KEY_TO_REGION.get(zone_key)
    url = generate_url(
        zone_key=zone_key,
        target_datetime=target_datetime,
    )

    req = (session or requests).get(url)
    req.raise_for_status()
    datasets = req.json()["data"]

    if additional_zone_key is not None:
        extra_url = generate_url(
            zone_key=additional_zone_key, target_datetime=target_datetime
        )
        extra_req = (session or requests).get(extra_url)
        extra_req.raise_for_status()
        extra_datasets = extra_req.json()["data"]
    else:
        extra_datasets = None

    breakpoint()
    filtered_datasets = [
        ds for ds in datasets if ds["type"] == data_type and ds["region"] == region
    ]
    df = pd.concat([dataset_to_df(ds) for ds in filtered_datasets], axis=1)
    breakpoint()

    # Sometimes we get twice the columns. In that case, only return the first one
    is_duplicated_column = df.columns.duplicated(keep="last")
    if is_duplicated_column.sum():
        logger.warning(
            f"Dropping columns {df.columns[is_duplicated_column]} that appear more than once"
        )
        df = df.loc[:, is_duplicated_column]

    return df


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_production(
    zone_key: str | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    df = fetch_main_power_df(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # Drop interconnectors
    df = df.drop([x for x in df.columns if "->" in x], axis=1)

    # Make sure charging is counted positively
    # and discharging negetively
    if "BATTERY_DISCHARGING" in df.columns:
        df["BATTERY_DISCHARGING"] = df["BATTERY_DISCHARGING"] * -1

    logger.info("Preparing final objects..")
    objs = [
        {
            "datetime": dt.to_pydatetime(),
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
            "source": SOURCE,
            "zoneKey": zone_key,
        }
        for dt, row in df.iterrows()
    ]

    objs = filter_production_objs(objs)

    # Validation
    logger.info("Validating..")
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
    session: Session | None = None,
    target_datetime: datetime | None = None,
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
            "datetime": dt.to_pydatetime(),
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
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    exchange_key = "->".join([zone_key1, zone_key2])

    try:
        exchange_params = EXCHANGE_MAPPING_DICTIONARY[exchange_key]
    except KeyError:
        raise ParserException(
            parser="OPENNEM",
            message=f"Valid exchange keys for this parser are {[EXCHANGE_MAPPING_DICTIONARY.keys()]}, you passed {exchange_key=}",
            zone_key=exchange_key,
        ) from None

    zone_key = exchange_params["zone_to_query"]
    additional_zone_key = exchange_params["additional_zone_to_query"]
    direction = exchange_params["direction"]

    df = fetch_main_power_df(
        zone_key=zone_key,
        additional_zone_key=additional_zone_key,
        direction=direction,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    breakpoint()
    direction = EXCHANGE_MAPPING_DICTIONARY[exchange_key]["direction"]

    # Take the first column (there's only one)
    series = df.iloc[:, 0]

    return [
        {
            "datetime": dt.to_pydatetime(),
            "netFlow": value * direction,
            "source": SOURCE,
            "sortedZoneKeys": exchange_key,
        }
        for dt, value in series.iteritems()
    ]


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""
    print(fetch_price("AU-SA"))

    print(fetch_production("AU-WA"))
    print(fetch_production("AU-NSW"))
    target_datetime = datetime.fromisoformat("2020-01-01T00:00:00+00:00")
    print(fetch_production("AU-SA", target_datetime=target_datetime))

    print(fetch_exchange("AU-SA", "AU-VIC"))
