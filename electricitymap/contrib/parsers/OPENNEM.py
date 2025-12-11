from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.utils import get_token

REFETCH_FREQUENCY = timedelta(days=7)
NETWORK_FETCH_WINDOW = timedelta(days=2)


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

# Reverse mapping from fuel type to category
PRODUCTION_MAPPING = {
    fuel_type.lower(): category
    for category, fuel_types in OPENNEM_PRODUCTION_CATEGORIES.items()
    for fuel_type in fuel_types
}
STORAGE_MAPPING = {
    fuel_type.lower(): category
    for category, fuel_types in OPENNEM_STORAGE_CATEGORIES.items()
    for fuel_type in fuel_types
}

IGNORED_FUEL_TECH_KEYS = {
    "imports",
    "exports",  # These keys are not relevant for production breakdowns
}

SOURCE = "opennem.org.au"


def fetch_datasets(
    zone_key: ZoneKey, session: Session, target_datetime: datetime | None
):
    region = ZONE_KEY_TO_REGION.get(zone_key)
    if not region:
        raise ParserException(
            parser="OPENNEM",
            message=f"Invalid zone_key {zone_key}, valid keys are {list(ZONE_KEY_TO_REGION.keys())}",
            zone_key=zone_key,
        )
    url = generate_url(
        zone_key=zone_key,
        target_datetime=target_datetime,
    )
    response = session.get(url)
    response.raise_for_status()

    return response.json()["data"]


def generate_url(zone_key: ZoneKey, target_datetime: datetime | None) -> str:
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


def process_production_datasets(
    datasets: list,
    zone_key: ZoneKey,
    logger: Logger,
) -> ProductionBreakdownList:
    """
    Process production datasets and return a production breakdown list.
    """
    now = datetime.now(tz=timezone.utc)
    unmerged_production_breakdown_lists = []
    region = ZONE_KEY_TO_REGION.get(zone_key)
    for dataset in datasets:
        if dataset["type"] != "power" or dataset["region"].upper() != region:
            continue
        mode = dataset.get("fuel_tech")

        if mode is None:
            continue
        if (
            mode
            not in PRODUCTION_MAPPING.keys()
            | STORAGE_MAPPING.keys()
            | IGNORED_FUEL_TECH_KEYS
        ):
            logger.error(
                f"Unknown fuel type {mode} in dataset {dataset['id']}, skipping."
            )
            continue
        if mode in IGNORED_FUEL_TECH_KEYS:
            continue
        production_breakdown_list = ProductionBreakdownList(logger=logger)
        history = dataset["history"]
        start = datetime.fromisoformat(history["start"])
        interval_min = int(history["interval"][:-1])  # remove 'm' at the end
        delta = timedelta(minutes=interval_min)
        data = history["data"]
        for i, value in enumerate(data):
            dt = start + i * delta
            if dt > now:
                logger.debug(
                    f"Skipping future datetime {dt} for zone {zone_key} in dataset {dataset['id']}"
                )
                continue
            if mode in PRODUCTION_MAPPING:
                production = ProductionMix()
                category = PRODUCTION_MAPPING[mode]
                production.add_value(
                    category,
                    value,
                    correct_negative_with_zero=True,
                )
                production_breakdown_list.append(
                    zoneKey=zone_key,
                    datetime=dt,
                    production=production,
                    source=SOURCE,
                )
            elif mode in STORAGE_MAPPING:
                storage = StorageMix()
                category = STORAGE_MAPPING[mode]
                multiplier = -1 if "discharging" in mode else 1
                value = value * multiplier if value is not None else None
                storage.add_value(
                    category,
                    value,
                )
                production_breakdown_list.append(
                    zoneKey=zone_key,
                    datetime=dt,
                    storage=storage,
                    source=SOURCE,
                )

        unmerged_production_breakdown_lists.append(production_breakdown_list)

    # Merge all production breakdown lists into one
    merged_production = ProductionBreakdownList.merge_production_breakdowns(
        unmerged_production_breakdown_lists,
        logger=logger,
    )

    # OPENNEM sometimes only report solar for the latest data, remove the datapoint if it only has solar
    # TODO: Remove this once the race condition between feeder-electricity and quality validation is fixed
    corrected_breakdown = ProductionBreakdownList(logger=logger)
    for event in merged_production:
        for mode, value in event.production.__dict__.items():
            if mode != "solar" and value is not None:
                dt = event.datetime
                production = event.production
                storage = event.storage
                source = event.source
                zoneKey = event.zoneKey
                corrected_breakdown.append(
                    zoneKey=zoneKey,
                    datetime=dt,
                    production=production,
                    storage=storage,
                    source=source,
                )
                break
    merged_production = corrected_breakdown
    return merged_production


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    session = session or Session()

    datasets = fetch_datasets(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
    )

    return process_production_datasets(
        datasets=datasets,
        zone_key=zone_key,
        logger=logger,
    ).to_list()


@refetch_frequency(NETWORK_FETCH_WINDOW)
def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
    target_datetime = target_datetime or datetime.now(tz=timezone.utc)

    datasets = _fetch_network_datasets(
        zone_key=zone_key,
        session=session,
        dataset_type="market",
        target_datetime=target_datetime,
        metrics=["price"],
    )

    price_list = _build_price_list(datasets, zone_key, logger)

    return price_list.to_list()


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
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
    zone_key: ZoneKey,
    direction: int,
    session: Session,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[tuple[datetime, float]]:
    """
    Calculate netflows for zones that have a single exchange.
    """
    url = generate_url(zone_key=zone_key, target_datetime=target_datetime)
    response = session.get(url)
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
    session: Session,
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
    nsw_zk = ZoneKey("AU-NSW")
    qld_zk = ZoneKey("AU-QLD")

    nsw_url = generate_url(zone_key=nsw_zk, target_datetime=target_datetime)
    qld_url = generate_url(zone_key=qld_zk, target_datetime=target_datetime)

    # potential race condition here
    # if the first request if right before a 5 minute interval and
    # the second request is right after then the responses could be out of sync
    # so we issue additional request as close to base request
    nsw_response = session.get(nsw_url)
    qld_response = session.get(qld_url)

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


def _build_network_url(
    path: str,
    network_code: str,
    metrics: list[str],
    target_datetime: datetime,
    network_region: str,
) -> tuple[str, dict[str, Any]]:
    base_url = f"https://api.openelectricity.org.au/v4/{path}/network/{network_code}"

    # API expects naive datetime in network-local time; target_datetime is UTC -> convert and drop tzinfo.
    def format_datetime(dt: datetime) -> str:
        local_dt = dt.astimezone(ZoneInfo("Australia/Sydney"))
        naive_dt = local_dt.replace(tzinfo=None)
        return naive_dt.isoformat()

    params = {
        "metrics": metrics,
        "date_start": format_datetime(target_datetime - NETWORK_FETCH_WINDOW),
        "date_end": format_datetime(target_datetime),
        "network_region": network_region,
    }

    return base_url, params


def _fetch_network_datasets(
    zone_key: str,
    session: Session,
    dataset_type: str,
    target_datetime: datetime,
    metrics: list[str],
) -> list[dict[str, Any]]:
    network_region = ZONE_KEY_TO_REGION.get(zone_key)
    network_code = ZONE_KEY_TO_NETWORK.get(zone_key)

    if not network_region or not network_code:
        raise ParserException(
            parser="OPENNEM",
            message=f"Invalid zone_key {zone_key}, valid keys are {list(ZONE_KEY_TO_REGION.keys())}",
            zone_key=zone_key,
        )

    url, params = _build_network_url(
        path=dataset_type,
        network_code=network_code,
        metrics=metrics,
        target_datetime=target_datetime,
        network_region=network_region,
    )

    token = get_token("OPENELECTRICITY_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = session.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()["data"]


def _build_price_list(datasets, zone_key: ZoneKey, logger: Logger) -> PriceList:
    price_list = PriceList(logger=logger)
    for dataset in datasets:
        if dataset["metric"] != "price":
            continue
        for result in dataset["results"]:
            for ts, price in result["data"]:
                price_list.append(
                    zoneKey=zone_key,
                    datetime=datetime.fromisoformat(ts),
                    currency="AUD",
                    price=price,
                    source=SOURCE,
                )

    return price_list


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""
    # print("fetch_price(zone_key='AU-SA') ->")
    # print(fetch_price(zone_key="AU-SA"))
    # print(fetch_production(ZoneKey("AU-TAS")))
    # print(fetch_production(ZoneKey("AU-NSW")))
    # target_datetime = datetime.fromisoformat("2020-01-01T00:00:00+00:00")
    # print(fetch_production(ZoneKey("AU-SA"), target_datetime=target_datetime))
    #
    # print(fetch_exchange(ZoneKey("AU-SA"), ZoneKey("AU-VIC")))
