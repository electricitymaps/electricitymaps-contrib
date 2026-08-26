from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from re import fullmatch
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.utils import get_token
from electricitymap.contrib.types import ZoneKey

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

# The API only reports flows aggregated per network region (`flow_imports` and
# `flow_exports`), never per interconnector, so exchanges are reconstructed from
# each region's net exports (exports - imports).
#
# Every region except NSW1 and VIC1 has a single interconnected neighbour, so
# its net exports are the netflow of that one exchange. See diagram below.
#       QLD
#        |
#       NSW
#        |
#   SA--VIC
#        |
#       TAS
#
# AU-NSW->AU-VIC is derived from the NSW and QLD flows. We want
#     AU-NSW->AU-VIC = NSW_exports_to_VIC - NSW_imports_from_VIC
#
# NSW has two exchanges, one to QLD and one to VIC:
#     NSW_exports = NSW_exports_to_QLD + NSW_exports_to_VIC
#     NSW_imports = NSW_imports_from_QLD + NSW_imports_from_VIC
#
# and because QLD only has one exchange, to NSW:
#     NSW_exports_to_QLD = QLD_imports_from_NSW = QLD_imports
#     NSW_imports_from_QLD = QLD_exports_to_NSW = QLD_exports
#
# thus
#     NSW_exports_to_VIC = NSW_exports - QLD_imports
#     NSW_imports_from_VIC = NSW_imports - QLD_exports
#
# and
#     AU-NSW->AU-VIC = NSW_exports - QLD_imports - NSW_imports + QLD_exports
#                    = (NSW_exports - NSW_imports) + (QLD_exports - QLD_imports)
#
# Each exchange below therefore maps the regions whose net exports make up its
# netflow to the coefficient each net export is weighted by.
EXCHANGE_MAPPING_DICTIONARY: dict[str, dict[str, int]] = {
    "AU-NSW->AU-QLD": {"QLD1": -1},
    "AU-SA->AU-VIC": {"SA1": 1},
    "AU-TAS->AU-VIC": {"TAS1": 1},
    "AU-NSW->AU-VIC": {"NSW1": 1, "QLD1": 1},
}

# Both are only served by the market endpoint; the data endpoint rejects them.
FLOW_IMPORTS_METRIC = "flow_imports"
FLOW_EXPORTS_METRIC = "flow_exports"

# Mapped from https://docs.openelectricity.org.au/guides/fueltechs#fueltechs
OPENNEM_PRODUCTION_CATEGORIES = {
    "coal": ["COAL_BLACK", "COAL_BROWN"],
    "gas": ["GAS_CCGT", "GAS_OCGT", "GAS_RECIP", "GAS_STEAM", "GAS_WCMG"],
    "oil": ["DISTILLATE"],
    "hydro": ["HYDRO"],
    "wind": ["WIND", "WIND_OFFSHORE"],
    "biomass": ["BIOENERGY_BIOGAS", "BIOENERGY_BIOMASS"],
    "solar": ["SOLAR_UTILITY", "SOLAR_ROOFTOP", "SOLAR_THERMAL"],
    "nuclear": ["NUCLEAR"],
}
OPENNEM_STORAGE_CATEGORIES = {
    # Storage
    "battery": ["BATTERY_DISCHARGING", "BATTERY_CHARGING", "BATTERY"],
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
    "exports",
    "interconnector",
    "aggregator_vpp",
    "aggregator_dr",
}

SOURCE = "opennem.org.au"

# Every OpenElectricity dataset carries an explicit resolution in its `interval`
# field, and every data point is stamped with AEMO's SETTLEMENTDATE, which labels
# the END of the interval it covers: the point stamped 14:35 covers 14:30-14:35.
# https://docs.openelectricity.org.au/guides/curtailment states the convention.
# Events therefore start one interval before the stamp.
_INTERVAL_UNIT_TO_KWARG = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}


def _interval_to_timedelta(interval: str) -> timedelta:
    """Convert an OpenElectricity interval string (e.g. '5m', '1h', '1d') to a timedelta.

    Months, quarters, seasons and years have no fixed length and are not
    supported; power, price and flow data is always reported at a fixed
    sub-daily resolution (typically '5m').
    """
    match = fullmatch(r"(\d+)([mhdw])", interval)
    if match is None:
        raise NotImplementedError(f"Unsupported OPENNEM interval: {interval!r}")
    value, unit = int(match.group(1)), match.group(2)
    return timedelta(**{_INTERVAL_UNIT_TO_KWARG[unit]: value})


def _dataset_resolution(
    dataset: dict[str, Any], zone_key: ZoneKey, logger: Logger
) -> timedelta | None:
    """Resolution a dataset declares, or None when it declares none."""
    interval = dataset.get("interval")
    if not interval:
        logger.warning(
            f"No interval on the {dataset.get('metric')} dataset for {zone_key}; "
            "timestamps are left on the source stamp instead of the interval start"
        )
        return None
    return _interval_to_timedelta(interval)


def _interval_bounds(
    stamp: datetime, resolution: timedelta | None
) -> tuple[datetime, datetime | None]:
    """Start and end of the interval a source stamp labels.

    Returns the stamp unchanged and no end when the resolution is unknown.
    """
    if resolution is None:
        return stamp, None
    return stamp - resolution, stamp


def process_production_datasets(
    datasets: list,
    zone_key: ZoneKey,
    logger: Logger,
) -> ProductionBreakdownList:
    """
    Process production datasets from v4 API endpoint and return a production breakdown list.
    v4 API format: data[].results[] with columns.fueltech and time series data as [timestamp, value] pairs.
    """
    now = datetime.now(tz=timezone.utc)
    unmerged_production_breakdown_lists = []

    # v4 API format: data[].results[] with columns.fueltech
    for dataset in datasets:
        if dataset.get("metric") != "power":
            continue

        resolution = _dataset_resolution(dataset, zone_key, logger)

        for result in dataset.get("results", []):
            columns = result.get("columns", {})
            fueltech = columns.get("fueltech")

            if not fueltech:
                continue

            # Map fueltech to our categories using existing mappings
            # v4 API fueltech values are like "COAL_BLACK", "GAS_CCGT", "BATTERY_CHARGING", etc.
            fueltech_key = fueltech.lower()

            if fueltech_key in IGNORED_FUEL_TECH_KEYS:
                continue

            # Map fueltech to category using existing PRODUCTION_MAPPING and STORAGE_MAPPING
            if fueltech_key in PRODUCTION_MAPPING:
                category = PRODUCTION_MAPPING[fueltech_key]
                is_production = True
                is_storage = False
            elif fueltech_key in STORAGE_MAPPING:
                category = STORAGE_MAPPING[fueltech_key]
                is_production = False
                is_storage = True
            else:
                raise ParserException(
                    parser="OPENNEM",
                    message=f"Unknown fueltech {fueltech} in result. Map it in OPENNEM_PRODUCTION_CATEGORIES or OPENNEM_STORAGE_CATEGORIES. See https://docs.openelectricity.org.au/guides/fueltechs#fueltechs",
                    zone_key=zone_key,
                )

            if category in IGNORED_FUEL_TECH_KEYS:
                continue

            production_breakdown_list = ProductionBreakdownList(logger=logger)
            time_series_data = result.get("data", [])

            for data_point in time_series_data:
                # v4 format: data is array of [timestamp, value] pairs
                if not isinstance(data_point, list) or len(data_point) < 2:
                    continue

                timestamp_str, value = data_point[0], data_point[1]

                # Parse timestamp (handle both with and without timezone)
                if timestamp_str.endswith("Z"):
                    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                elif "+" in timestamp_str or timestamp_str.count("-") >= 3:
                    # Has timezone info
                    dt = datetime.fromisoformat(timestamp_str)
                else:
                    # No timezone, assume it's in Australia/Sydney timezone
                    dt = datetime.fromisoformat(timestamp_str)
                    if not dt.tzinfo:
                        dt = dt.replace(tzinfo=ZoneInfo("Australia/Sydney"))

                if dt > now:
                    logger.debug(f"Skipping future datetime {dt} for zone {zone_key}")
                    continue

                if value is None:
                    continue

                interval_start, interval_end = _interval_bounds(dt, resolution)

                if is_production:
                    production = ProductionMix()
                    production.add_value(
                        category,
                        value,
                        correct_negative_with_zero=True,
                    )
                    production_breakdown_list.append(
                        zoneKey=zone_key,
                        datetime=interval_start,
                        end_datetime=interval_end,
                        production=production,
                        source=SOURCE,
                    )
                elif is_storage:
                    storage = StorageMix()
                    # For storage, we want to treat discharging as positive and charging as negative, so we flip the sign for discharging fueltechs
                    # Refrence: https://docs.openelectricity.org.au/guides/batteries
                    multiplier = (
                        -1
                        if ("discharging" in fueltech_key or fueltech_key == "battery")
                        else 1
                    )
                    value = value * multiplier if value is not None else None
                    storage.add_value(
                        category,
                        value,
                    )
                    production_breakdown_list.append(
                        zoneKey=zone_key,
                        datetime=interval_start,
                        end_datetime=interval_end,
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
                    end_datetime=event.end_datetime,
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

    # Get network_region for the zone (will be included if available)
    network_region = ZONE_KEY_TO_REGION.get(zone_key)

    # For v4 API, we can pass None for target_datetime to get latest data without date params
    # Only include dates if specifically requested
    datasets = _fetch_network_datasets(
        zone_key=zone_key,
        session=session,
        dataset_type="data",
        target_datetime=target_datetime,  # Pass None to get latest data without date params
        metrics=["power"],
        secondary_grouping="fueltech",
        network_region=network_region,  # Include network_region if available
    )

    return process_production_datasets(
        datasets=datasets,
        zone_key=zone_key,
        logger=logger,
    ).to_list()


@refetch_frequency(REFETCH_FREQUENCY)
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
        network_region=ZONE_KEY_TO_REGION.get(zone_key),
    )

    price_list = _build_price_list(datasets, zone_key, logger)

    return price_list.to_list()


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetch actual regional demand (MW) from the Open Electricity v4 market API.

    Open Electricity does not currently expose consumption *forecasts* on v4
    (see opennem/opennem#500). Keep AEMO.fetch_consumption_forecast for
    forecasted demand; this parser covers observed load only.
    """
    session = session or Session()
    target_datetime = target_datetime or datetime.now(tz=timezone.utc)

    datasets = _fetch_network_datasets(
        zone_key=zone_key,
        session=session,
        dataset_type="market",
        target_datetime=target_datetime,
        metrics=["demand"],
        network_region=ZONE_KEY_TO_REGION.get(zone_key),
    )

    return _build_consumption_list(datasets, zone_key, logger).to_list()


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
        region_coefficients = EXCHANGE_MAPPING_DICTIONARY[exchange_key]
    except KeyError:
        raise ParserException(
            parser="OPENNEM",
            message=f"Valid exchange keys for this parser are {list(EXCHANGE_MAPPING_DICTIONARY.keys())}, you passed {exchange_key=}",
            zone_key=exchange_key,
        ) from None

    # A single request returns every region's imports and exports on one shared
    # set of timestamps, so the terms of the sums are aligned by construction.
    datasets = _fetch_network_datasets(
        zone_key=zone_key1,
        session=session,
        dataset_type="market",
        target_datetime=target_datetime,
        metrics=[FLOW_IMPORTS_METRIC, FLOW_EXPORTS_METRIC],
        primary_grouping="network_region",
    )
    net_exports = _build_region_net_exports(datasets)
    resolution = _flow_resolution(datasets, exchange_key)

    missing_regions = [
        region for region in region_coefficients if not net_exports.get(region)
    ]
    if missing_regions:
        raise ParserException(
            parser="OPENNEM",
            message=f"Response did not contain both import and export data for {missing_regions}",
            zone_key=exchange_key,
        )

    # Only datetimes every region reported can be summed; a term missing from
    # the sum would understate the netflow rather than show up as missing.
    common = set.intersection(
        *(set(net_exports[region]) for region in region_coefficients)
    )
    contributions = []
    for region, coefficient in region_coefficients.items():
        events = ExchangeList(logger=logger)
        for dt in common:
            interval_start, interval_end = _interval_bounds(dt, resolution)
            events.append(
                datetime=interval_start,
                end_datetime=interval_end,
                netFlow=coefficient * net_exports[region][dt],
                zoneKey=exchange_key,
                source=SOURCE,
            )
        contributions.append(events)

    return ExchangeList.merge_exchanges(contributions, logger).to_list()


def _build_region_net_exports(
    datasets: list[dict[str, Any]],
) -> dict[str, dict[datetime, float]]:
    """
    Build each network region's net exports (exports - imports) per datetime from
    the flow datasets of the market endpoint.

    Datetimes where either side is missing or null are dropped.
    """
    flows: dict[str, dict[str, dict[datetime, float]]] = {}
    for dataset in datasets:
        metric = dataset.get("metric")
        if metric not in (FLOW_IMPORTS_METRIC, FLOW_EXPORTS_METRIC):
            continue
        for result in dataset.get("results", []):
            region = result.get("columns", {}).get("region")
            if not region:
                continue
            series = flows.setdefault(region, {}).setdefault(metric, {})
            for data_point in result.get("data", []):
                if not isinstance(data_point, list) or len(data_point) < 2:
                    continue
                timestamp, value = data_point[0], data_point[1]
                if value is None:
                    continue
                series[datetime.fromisoformat(timestamp)] = float(value)

    net_exports: dict[str, dict[datetime, float]] = {}
    for region, metrics in flows.items():
        imports = metrics.get(FLOW_IMPORTS_METRIC, {})
        exports = metrics.get(FLOW_EXPORTS_METRIC, {})
        net_exports[region] = {
            dt: exports[dt] - imports[dt] for dt in exports.keys() & imports.keys()
        }
    return net_exports


def _flow_resolution(
    datasets: list[dict[str, Any]], exchange_key: ZoneKey
) -> timedelta | None:
    """
    Resolution shared by the flow datasets, used to place the interval bounds.

    Raises if the flow datasets report different intervals.
    """
    intervals = {
        dataset["interval"]
        for dataset in datasets
        if dataset.get("metric") in (FLOW_IMPORTS_METRIC, FLOW_EXPORTS_METRIC)
        and dataset.get("interval")
    }
    if len(intervals) > 1:
        raise ParserException(
            parser="OPENNEM",
            message=f"Import and export data is reported at different intervals: {sorted(intervals)}",
            zone_key=exchange_key,
        )
    return _interval_to_timedelta(intervals.pop()) if intervals else None


def _build_network_url(
    path: str,
    network_code: str,
    metrics: list[str],
    target_datetime: datetime | None,
    network_region: str | None = None,
    primary_grouping: str | None = None,
    secondary_grouping: str | None = None,
) -> tuple[str, dict[str, Any]]:
    base_url = f"https://api.openelectricity.org.au/v4/{path}/network/{network_code}"

    params: dict[str, Any] = {
        "metrics": metrics,
    }

    # Add date range only if target_datetime is explicitly provided
    # If None, API will return latest available data
    if target_datetime:
        # API expects naive datetime in network-local time; target_datetime is UTC -> convert and drop tzinfo.
        def format_datetime(dt: datetime) -> str:
            local_dt = dt.astimezone(ZoneInfo("Australia/Sydney"))
            naive_dt = local_dt.replace(tzinfo=None)
            return naive_dt.isoformat()

        params["date_start"] = format_datetime(target_datetime - REFETCH_FREQUENCY)
        params["date_end"] = format_datetime(target_datetime)

    # Add network_region only if provided (not required for production data endpoint)
    if network_region:
        params["network_region"] = network_region

    # Add primary_grouping if provided (to get one series per network region)
    if primary_grouping:
        params["primary_grouping"] = primary_grouping

    # Add secondary_grouping if provided (for production data with fueltech)
    if secondary_grouping:
        params["secondary_grouping"] = secondary_grouping

    return base_url, params


def _fetch_network_datasets(
    zone_key: str,
    session: Session,
    dataset_type: str,
    target_datetime: datetime | None,
    metrics: list[str],
    primary_grouping: str | None = None,
    secondary_grouping: str | None = None,
    network_region: str | None = None,
) -> list[dict[str, Any]]:
    network_code = ZONE_KEY_TO_NETWORK.get(zone_key)

    if not network_code:
        raise ParserException(
            parser="OPENNEM",
            message=f"Invalid zone_key {zone_key}, valid keys are {list(ZONE_KEY_TO_NETWORK.keys())}",
            zone_key=zone_key,
        )

    url, params = _build_network_url(
        path=dataset_type,
        network_code=network_code,
        metrics=metrics,
        target_datetime=target_datetime or datetime.now(tz=timezone.utc),
        network_region=network_region,
        primary_grouping=primary_grouping,
        secondary_grouping=secondary_grouping,
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
        resolution = _dataset_resolution(dataset, zone_key, logger)
        for result in dataset["results"]:
            for ts, price in result["data"]:
                interval_start, interval_end = _interval_bounds(
                    datetime.fromisoformat(ts), resolution
                )
                price_list.append(
                    zoneKey=zone_key,
                    datetime=interval_start,
                    end_datetime=interval_end,
                    currency="AUD",
                    price=price,
                    source=SOURCE,
                )

    return price_list


def _build_consumption_list(
    datasets, zone_key: ZoneKey, logger: Logger
) -> TotalConsumptionList:
    now = datetime.now(tz=timezone.utc)
    consumption_list = TotalConsumptionList(logger=logger)
    for dataset in datasets:
        if dataset.get("metric") != "demand":
            continue
        resolution = _dataset_resolution(dataset, zone_key, logger)
        for result in dataset.get("results", []):
            for data_point in result.get("data", []):
                if not isinstance(data_point, list) or len(data_point) < 2:
                    continue
                timestamp_str, value = data_point[0], data_point[1]
                if value is None:
                    continue
                dt = datetime.fromisoformat(timestamp_str)
                if dt > now:
                    logger.debug(f"Skipping future datetime {dt} for zone {zone_key}")
                    continue
                interval_start, interval_end = _interval_bounds(dt, resolution)
                consumption_list.append(
                    zoneKey=zone_key,
                    datetime=interval_start,
                    end_datetime=interval_end,
                    consumption=float(value),
                    source=SOURCE,
                )

    return consumption_list


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
    # print(fetch_consumption(ZoneKey("AU-NSW")))
