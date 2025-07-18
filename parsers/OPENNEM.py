from datetime import datetime, timedelta
from logging import Logger, getLogger

import pandas as pd
import requests
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.lib.models.events import Exchange
from electricitymap.contrib.lib.types import ZoneKey
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
        "direction": -1,
    },
    "AU-SA->AU-VIC": {
        "zone_to_query": "AU-SA",
        "direction": 1,
    },
    "AU-TAS->AU-VIC": {
        "zone_to_query": "AU-TAS",
        "direction": 1,
    },
    # we get this flow by substracting QLD imports/exports from NSW imports/exports
    "AU-NSW->AU-VIC": {
        "zone_to_query": "AU-NSW",
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
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    return _fetch_main_df(
        "price",
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


def fetch_main_power_df(
    zone_key: str | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> tuple[pd.DataFrame, list]:
    return _fetch_main_df(
        "power",
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


def _fetch_main_df(
    data_type,
    zone_key: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger | None = None,
) -> tuple[pd.DataFrame, list]:
    region = ZONE_KEY_TO_REGION.get(zone_key)
    url = generate_url(
        zone_key=zone_key,
        target_datetime=target_datetime,
    )

    response = (session or requests).get(url)
    response.raise_for_status()
    datasets = response.json()["data"]

    filtered_datasets = [
        ds
        for ds in datasets
        if ds["type"] == data_type and ds["region"].upper() == region
    ]
    df = pd.concat([dataset_to_df(ds) for ds in filtered_datasets], axis=1)

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
) -> list[Exchange]:
    exchange_key = ZoneKey("->".join([zone_key1, zone_key2]))

    try:
        exchange_params = EXCHANGE_MAPPING_DICTIONARY[exchange_key]
    except KeyError:
        raise ParserException(
            parser="OPENNEM",
            message=f"Valid exchange keys for this parser are {[EXCHANGE_MAPPING_DICTIONARY.keys()]}, you passed {exchange_key=}",
            zone_key=exchange_key,
        ) from None

    zone_key = exchange_params["zone_to_query"]
    direction = exchange_params["direction"]

    if exchange_key == "AU-NSW->AU-VIC":
        datetimes_and_netflows = _fetch_au_nsw_au_vic_exchange(
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
    else:
        datetimes_and_netflows = _fetch_regular_exchange(
            zone_key=zone_key,
            direction=direction,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )

    events = ExchangeList(logger=logger)
    for dt, netflow in datetimes_and_netflows:
        events.append(datetime=dt, netFlow=netflow, zoneKey=exchange_key, source=SOURCE)
    return events.to_list()


def _fetch_regular_exchange(
    zone_key=str,
    direction=int,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[tuple[datetime, float]]:
    """
    Calculate netflows for zones that have a single exchange.
    """
    url = generate_url(zone_key=zone_key, target_datetime=target_datetime)
    response = (session or requests).get(url)
    response.raise_for_status()

    exports = None
    imports = None
    for dataset in response.json()["data"]:
        if dataset["id"].endswith("exports.power"):
            exports = dataset.get("history", None)
        elif dataset["id"].endswith("imports.power"):
            imports = dataset.get("history", None)
        else:
            continue
    if exports is None or imports is None:
        raise ParserException(
            parser="OPENNEM",
            message="Response did not contain both export and import datasets.",
            zone_key=zone_key,
        )

    if (
        exports["start"] != imports["start"]
        or exports["last"] != imports["last"]
        or len(exports["data"]) != len(imports["data"])
    ):
        raise ParserException(
            parser="OPENNEM",
            message="Export and import data is misaligned",
            zone_key=zone_key,
        )

    # assume data is sorted from start to end
    start = datetime.fromisoformat(exports["start"])
    datetimes_and_netflows = [
        (start + timedelta(minutes=5 * i), (exp - imp) * direction)
        for i, (exp, imp) in enumerate(
            zip(exports["data"], imports["data"], strict=True)
        )
    ]

    return datetimes_and_netflows


def _fetch_au_nsw_au_vic_exchange(
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[tuple[datetime, float]]:
    """
    Calculate AU-NSW->AU-VIC netflow from exports and imports of AU-NSW and AU-QLD.

    NSW has two exchanges one to QLD, one to VIC. QLD only has one exchange to NSW.
    We want to know
        AU-NSW->AU-VIC = NSW_exports_to_VIC - NSW_imports_from_VIC

    NSW has two exchanges one to QLD, one to VIC:
        NSW_exports = NSW_exports_to_QLD + NSW_exports_to_VIC
        NSW_imports = NSW_imports_from_QLD + NSW_imports_from_VIC

    and because QLD only has one exchange to NSW:
        NSW_exports_to_QLD = QLD_imports_from_NSW = QLD_imports
        NSW_imports_from_QLD = QLD_exports_to_NSW = QLD_exports

    thus
        NSW_exports_to_VIC = NSW_exports - QLD_imports
        NSW_imports_from_VIC = NSW_imports - QLD_exports

    and
        AU-NSW->AU-VIC = NSW_exports - QLD_imports - NSW_imports + QLD_exports
        = NSW_exports - NSW_imports + QLD_exports - QLD_imports
    """
    nsw_zk = "AU-NSW"
    qld_zk = "AU-QLD"

    nsw_url = generate_url(zone_key=nsw_zk, target_datetime=target_datetime)
    qld_url = generate_url(zone_key=qld_zk, target_datetime=target_datetime)

    # potential race condition here
    # if the first request if right before a 5 minute interval and
    # the second request is right after then the responses could be out of sync
    # so we issue additional request as close to base request
    nsw_response = (session or requests).get(nsw_url)
    qld_response = (session or requests).get(qld_url)

    nsw_response.raise_for_status()
    qld_response.raise_for_status()

    nsw_exports = None
    nsw_imports = None
    for dataset in nsw_response.json()["data"]:
        if dataset["id"].endswith("exports.power"):
            nsw_exports = dataset.get("history", None)
        elif dataset["id"].endswith("imports.power"):
            nsw_imports = dataset.get("history", None)
        else:
            continue
    if nsw_exports is None or nsw_imports is None:
        raise ParserException(
            parser="OPENNEM",
            message="Response did not contain both export and import datasets.",
            zone_key=nsw_zk,
        )

    qld_exports = None
    qld_imports = None
    for dataset in qld_response.json()["data"]:
        if dataset["id"].endswith("exports.power"):
            qld_exports = dataset.get("history", None)
        elif dataset["id"].endswith("imports.power"):
            qld_imports = dataset.get("history", None)
        else:
            continue
    if qld_exports is None or qld_imports is None:
        raise ParserException(
            parser="OPENNEM",
            message="Response did not contain both export and import datasets.",
            zone_key=qld_zk,
        )

    # all must have same start, end, and number of data points
    if not (
        nsw_exports["start"]
        == nsw_imports["start"]
        == qld_exports["start"]
        == qld_imports["start"]
        and nsw_exports["last"]
        == nsw_imports["last"]
        == qld_exports["last"]
        == qld_imports["last"]
        and len(nsw_exports["data"])
        == len(nsw_imports["data"])
        == len(qld_exports["data"])
        == len(qld_imports["data"])
    ):
        raise ParserException(
            parser="OPENNEM",
            message=f"{nsw_zk} and {qld_zk} export and import data is misaligned",
            zone_key=nsw_zk,
        )

    # assume data is sorted from start to end
    start = datetime.fromisoformat(nsw_exports["start"])
    datetimes_and_netflows = [
        (start + timedelta(minutes=5 * i), (nsw_exp - nsw_imp + qld_exp - qld_imp))
        for i, (nsw_exp, nsw_imp, qld_exp, qld_imp) in enumerate(
            zip(
                nsw_exports["data"],
                nsw_imports["data"],
                qld_exports["data"],
                qld_imports["data"],
                strict=True,
            )
        )
    ]

    return datetimes_and_netflows


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""
    print(fetch_price("AU-SA"))

    print(fetch_production("AU-WA"))
    print(fetch_production("AU-NSW"))
    target_datetime = datetime.fromisoformat("2020-01-01T00:00:00+00:00")
    print(fetch_production("AU-SA", target_datetime=target_datetime))

    print(fetch_exchange("AU-SA", "AU-VIC"))
