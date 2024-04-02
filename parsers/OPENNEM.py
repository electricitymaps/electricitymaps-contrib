from collections.abc import Mapping
from datetime import datetime, timedelta
from logging import Logger, getLogger

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency

CURRENCY = "AUD"

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
    "battery": ["BATTERY_DISCHARGING", "BATTERY_CHARGING"],
    "hydro": ["PUMPS"],
}
SOURCE = "opennem.org.au"


def dataset_to_df(dataset: dict) -> pd.DataFrame:
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
    assert len(index) == len(series["data"])
    df = pd.DataFrame(index=index, data=series["data"], columns=[name])

    return df


def process_solar_rooftop(df: pd.DataFrame) -> pd.DataFrame:
    if "SOLAR_ROOFTOP" in df:
        # at present, solar rooftop data comes in each 30 mins.
        # Resample data to not require interpolation
        return df.resample("30T").mean()
    return df


def get_capacities(filtered_datasets: list[Mapping], region: str) -> pd.Series:
    # Parse capacity data
    capacities = {
        obj["id"].split(".")[-2].upper(): obj.get("x_capacity_at_present")
        for obj in filtered_datasets
        if obj["region"] == region
    }
    return pd.Series(capacities)


def sum_vector(
    pd_series: pd.Series, keys: list[str], ignore_nans: bool = False
) -> pd.Series | None:
    # Only consider keys that are in the pd_series
    filtered_keys = pd_series.index.intersection(keys)

    # Require all present keys to be non-null
    pd_series_filtered = pd_series.loc[filtered_keys]
    nan_filter = pd_series_filtered.notnull().all() | ignore_nans
    if filtered_keys.size and nan_filter:
        return pd_series_filtered.fillna(0).sum()
    else:
        return None


def filter_production_item(mode: str, value: int | float | None) -> bool:
    """Flags production key/value pairs that should be filtered out."""

    # filter out entries that have solar None
    if mode == "solar" and value is None:
        return True

    return False


def generate_url(
    zone_key: ZoneKey,
    is_flow: bool,
    target_datetime: datetime | None,
) -> str:
    if target_datetime is None:
        # Get latest data, contains flows and production combined
        return "https://data.opennem.org.au/v3/clients/em/latest.json"

    # ... else will fetch since the beginning of the current month
    month = target_datetime.strftime("%Y-%m-%d")
    network = ZONE_KEY_TO_NETWORK[zone_key]
    if is_flow:
        return f"http://api.opennem.org.au/stats/flow/network/{network}?month={month}"
    else:
        region = ZONE_KEY_TO_REGION.get(zone_key)
        return f"http://api.opennem.org.au/stats/power/network/fueltech/{network}/{region}?month={month}"


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
    )[0]


def fetch_main_power_df(
    zone_key: str | None = None,
    sorted_zone_keys: str | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> tuple[pd.DataFrame, list]:
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
    zone_key: ZoneKey | None,
    sorted_zone_keys: ZoneKey | None,
    session: Session | None,
    target_datetime: datetime | None,
    logger: Logger,
) -> tuple[pd.DataFrame, list]:
    url = generate_url(
        zone_key=zone_key or sorted_zone_keys.split("->")[0],
        is_flow=sorted_zone_keys is not None,
        target_datetime=target_datetime,
    )

    # Fetches the last week of data
    logger.info(f"Requesting {url}..")
    session = session or Session()
    response = session.get(url)
    response.raise_for_status()
    logger.debug("Parsing JSON..")
    datasets = response.json()["data"]
    logger.debug("Filtering datasets..")

    region = ZONE_KEY_TO_REGION.get(zone_key)

    def filter_dataset(ds: dict) -> bool:
        filter_data_type = ds["type"] == data_type
        filter_region = False
        if zone_key:
            filter_region |= ds.get("region") == region
        if sorted_zone_keys:
            filter_region |= (
                ds.get("id").split(".")[-2]
                == EXCHANGE_MAPPING_DICTIONARY[sorted_zone_keys]["region_id"]
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
    zone_key: ZoneKey = ZoneKey("AU-SA"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    df, filtered_datasets = fetch_main_power_df(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # Drop interconnectors
    df = df.drop([x for x in df.columns if "->" in x], axis=1)
    # Make sure charging is counted positively and discharging negatively
    if "BATTERY_DISCHARGING" in df.columns:
        df["BATTERY_DISCHARGING"] = df["BATTERY_DISCHARGING"] * -1

    logger.debug("Preparing final objects..")
    production_list = ProductionBreakdownList(logger)
    for dt, row in df.iterrows():
        dtime = dt.to_pydatetime()

        production_mix = ProductionMix()
        for production_mode in [
            "coal",
            "gas",
            "oil",
            "hydro",
            "wind",
            "biomass",
            # Here we assume all rooftop solar is fed to the grid
            # This assumption should be checked and we should here only report grid-level generation
            "solar",
        ]:
            production_value = sum_vector(
                row, OPENNEM_PRODUCTION_CATEGORIES[production_mode]
            )

            logger.debug("Filtering..")
            if filter_production_item(mode=production_mode, value=production_value):
                logger.warning(
                    f"Entry for {dtime} is dropped because it does not pass the production filter."
                )
                continue

            logger.debug("Validating..")
            if production_value is not None and -50 < production_value < 0:
                logger.warning(
                    f"Setting small value of {production_mode} ({production_value}) to 0.",
                    extra={"key": zone_key},
                )
                production_value = 0.0

            production_mix.add_value(production_mode, production_value)

        storage_mix = StorageMix()
        for storage_mode in [
            # opennem reports battery charging as negative, we here should report as positive
            # we made the sign switch before, so we can just sum them up
            "battery",
            # opennem reports hydro pumping as positive, we here should report as positive
            "hydro",
        ]:
            storage_value = sum_vector(row, OPENNEM_STORAGE_CATEGORIES[storage_mode])
            storage_mix.add_value(storage_mode, storage_value)

        production_list.append(
            zoneKey=zone_key,
            datetime=dtime,
            production=production_mix,
            storage=storage_mix,
            source=SOURCE,
        )

    return production_list.to_list()


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_price(
    zone_key: ZoneKey = ZoneKey("AU-SA"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    df = fetch_main_price_df(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    df = df.loc[~df["PRICE"].isna()]  # Only keep prices that are defined

    price_list = PriceList(logger)
    for dt, row in df.iterrows():
        price_list.append(
            zoneKey=zone_key,
            datetime=dt.to_pydatetime(),
            currency=CURRENCY,
            price=sum_vector(row, ["PRICE"]),  # currency / MWh,
            source=SOURCE,
        )
    return price_list.to_list()


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    direction = EXCHANGE_MAPPING_DICTIONARY[sorted_zone_keys]["direction"]

    df, _ = fetch_main_power_df(
        sorted_zone_keys=sorted_zone_keys,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # Take the first column (there's only one)
    series = df.iloc[:, 0]

    exchange_list = ExchangeList(logger)
    for dt, value in series.iteritems():
        exchange_list.append(
            zoneKey=sorted_zone_keys,
            datetime=dt.to_pydatetime(),
            netFlow=value * direction,
            source=SOURCE,
        )
    return exchange_list.to_list()


if __name__ == "__main__":
    print(fetch_price(ZoneKey("AU-SA")))

    print(fetch_production(ZoneKey("AU-WA")))
    print(fetch_production(ZoneKey("AU-NSW")))
    target_datetime = datetime.fromisoformat("2020-01-01T00:00:00+00:00")
    print(fetch_production(ZoneKey("AU-SA"), target_datetime=target_datetime))

    print(fetch_exchange(ZoneKey("AU-SA"), ZoneKey("AU-VIC")))
