#!/usr/bin/env python3

"""
Parser that uses the ELEXON API to return the following data types.

Production
Exchanges

Documentation:
https://bscdocs.elexon.co.uk/guidance-notes/bmrs-api-and-data-push-user-guide
"""

import re
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Any

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

ELEXON_API_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1"
ELEXON_URLS = {
    "production_fuelhh": "/".join((ELEXON_API_ENDPOINT, "datasets/FUELINST/stream")),
    "exchange": "/".join((ELEXON_API_ENDPOINT, "generation/outturn/interconnectors")),
    "balancing": "/".join((ELEXON_API_ENDPOINT, "balancing/physical")),
    "actual_load": "/".join(
        (ELEXON_API_ENDPOINT, "datasets/ATL/stream")
    ),  # B0610 - Actual Total Load https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/ATL
}
ELEXON_START_DATE = datetime(
    2019, 1, 1, tzinfo=timezone.utc
)  # ELEXON API only has data from 2019-01-01
ELEXON_SOURCE = "elexon.co.uk"
ESO_NATIONAL_GRID_ENDPOINT = (
    "https://api.nationalgrideso.com/api/3/action/datastore_search_sql"
)
ESO_SOURCE = "nationalgrideso.com"

# A specific report to query most recent data (within 1 month time span + forecast ahead)
ESO_DEMAND_DATA_UPDATE_ID = "177f6fa4-ae49-4182-81ea-0c6b35f26ca6"

# 'hydro' key is for hydro production
# 'hydro storage' key is for hydro storage
RESOURCE_TYPE_TO_FUEL = {
    "Biomass": "biomass",
    "Fossil Gas": "gas",
    "Fossil Hard coal": "coal",
    "Fossil Oil": "oil",
    "Hydro Pumped Storage": "hydro storage",
    "Hydro Run-of-river and poundage": "hydro",
    "Nuclear": "nuclear",
    "Solar": "solar",
    "Wind Onshore": "wind",
    "Wind Offshore": "wind",
    "Other": "unknown",
}
# Mapping is ordered to match the FUELINST output file as there's no header.
FUEL_INST_MAPPING = {
    "CCGT": "gas",
    "OIL": "oil",
    "COAL": "coal",
    "NUCLEAR": "nuclear",
    "WIND": "wind",
    "PS": "solar",
    "NPSHYD": "hydro",
    "OCGT": "gas",
    "OTHER": "unknown",
    "INTFR": "exchange",  # IFA (France)
    "INTIRL": "exchange",  # Northen Ireland
    "INTGRNL": "exchange",  # Greenlink (Ireland)
    "INTNED": "exchange",  # BritNed (Netherlands)
    "INTEW": "exchange",  # East West (Ireland)
    "BIOMASS": "biomass",
    "INTNEM": "exchange",  # Nemolink (Belgium)
    "INTELEC": "exchange",  # Eleclink (France)
    "INTIFA2": "exchange",  # IFA2 (France)
    "INTNSL": "exchange",  # North Sea Link (Norway)
    "INTVKL": "exchange",  # Viking Link (Denmark)
}

ESO_FUEL_MAPPING = {
    "EMBEDDED_WIND_GENERATION": "wind",
    "EMBEDDED_SOLAR_GENERATION": "solar",
    "PUMP_STORAGE_PUMPING": "hydro storage",
}

ZONEKEY_TO_INTERCONNECTOR = {
    "BE->GB": ["Belgium (Nemolink)"],
    "DK-DK1->GB": ["Denmark (Viking link)"],
    "FR->GB": ["Eleclink (INTELEC)", "France(IFA)", "IFA2 (INTIFA2)"],
    "GB->GB-NIR": ["Northern Ireland(Moyle)"],
    "GB->IE": ["Ireland(East-West)", "Ireland (Greenlink)"],
    "GB->NL": ["Netherlands(BritNed)"],
    "GB->NO-NO2": ["North Sea Link (INTNSL)"],
}

# Change direction of exchange for connectors where data is from Elexon and zonekey "GB->*". Due to Elexon showing wrt UK
EXHANGE_KEY_IS_IMPORT = {
    "BE->GB": False,
    "DK-DK1->GB": False,
    "FR->GB": False,
    "GB->GB-NIR": False,
    "GB->IE": True,
    "GB->NL": True,
    "GB->NO-NO2": False,
}


def zulu_to_utc(datetime_str: str) -> str:
    return datetime_str.replace("Z", "+00:00")


def query_elexon(url: str, session: Session, params: dict) -> list | dict:
    r: Response = session.get(url, params=params)
    if not r.ok:
        raise ParserException(
            parser="ELEXON",
            message=f"Error fetching data: {r.status_code} {r.reason}",
        )
    return r.json()


def parse_datetime(
    settlementDate: str | None, settlementPeriod: int | None
) -> datetime:
    if settlementDate is None or settlementPeriod is None:
        raise ParserException(
            parser="ELEXON",
            message="Error fetching data: settlementDate or settlementPeriod is None",
        )
    parsed_datetime = datetime.strptime(settlementDate, "%Y-%m-%d")
    parsed_datetime += timedelta(hours=(settlementPeriod - 1) / 2)
    return parsed_datetime.replace(tzinfo=timezone.utc)


def query_IM_exchange(
    session: Session, target_datetime: datetime, logger: Logger
) -> ExchangeList:
    """
    Fetches balancing mechanism data from the ELEXON API.
    This is used to get the imbalance quantity for the GB->IM interconnector.
    """
    bm_unit = "MANXENR-1"
    balancing_params = {
        "bmUnit": bm_unit,
        "dataset": "PN",  # Physical data
        "from": (target_datetime - timedelta(days=2)).strftime("%Y-%m-%d"),
        "to": (target_datetime + timedelta(days=1)).strftime("%Y-%m-%d"),
    }
    balancing_data = query_elexon(ELEXON_URLS["balancing"], session, balancing_params)

    exchange_list = ExchangeList(logger)
    if isinstance(balancing_data, dict):
        for event in balancing_data.get("data", []):
            event_datetime = datetime.fromisoformat(
                event["timeFrom"].replace("Z", "+00:00")
            )
            exchange_list.append(
                zoneKey=ZoneKey("GB->IM"),
                netFlow=event.get("levelFrom") * -1,
                source=ELEXON_SOURCE,
                datetime=event_datetime,
            )
    return exchange_list


def get_event_value(event: dict[str, Any], key: str) -> float | None:
    value = event.get(key)
    if value is not None:
        return float(value)


def parse_production(
    production_data: list[dict[str, Any]], logger: Logger, dataset: str
) -> ProductionBreakdownList:
    """Parses production events from the ELEXON API. This function is used for the B1620 data or the FUELHH data."""
    dataset_info = {
        "B1620": {
            "mode_mapping": RESOURCE_TYPE_TO_FUEL,
            "mode_key": "psrType",
            "quantity_key": "quantity",
        },
        "FUELHH": {
            "mode_mapping": FUEL_INST_MAPPING,
            "mode_key": "fuelType",
            "quantity_key": "generation",
        },
    }

    mode_mapping = dataset_info[dataset]["mode_mapping"]
    mode_key = dataset_info[dataset]["mode_key"]
    quantity_key = dataset_info[dataset]["quantity_key"]

    all_production_breakdowns: list[ProductionBreakdownList] = []

    for event in production_data:
        production_breakdown = ProductionBreakdownList(logger=logger)
        event_datetime_str = event.get("startTime")
        production_mix = ProductionMix()
        storage_mix = StorageMix()

        production_mode = mode_mapping[event.get(mode_key)]

        if production_mode == "exchange":
            continue

        if production_mode == "hydro storage":
            storage_value = get_event_value(event, quantity_key)
            if storage_value is not None:
                storage_mix.add_value("hydro", -1 * storage_value)

        else:
            production_value = get_event_value(event, quantity_key)
            production_mix.add_value(
                production_mode, production_value, correct_negative_with_zero=True
            )
        if event_datetime_str:
            event_datetime = datetime.fromisoformat(zulu_to_utc(event_datetime_str))
            production_breakdown.append(
                zoneKey=ZoneKey("GB"),
                production=production_mix,
                storage=storage_mix,
                source=ELEXON_SOURCE,
                datetime=event_datetime,
            )

        all_production_breakdowns.append(production_breakdown)
    events = ProductionBreakdownList.merge_production_breakdowns(
        all_production_breakdowns, logger
    )
    return events


def _create_eso_historical_demand_index(session: Session) -> dict[int, str]:
    """Get the ids of all historical_demand_data reports"""
    index = {}
    response = session.get(
        "https://data.nationalgrideso.com/demand/historic-demand-data/datapackage.json"
    )
    data = response.json()
    pattern = re.compile(r"historic_demand_data_(?P<year>\d+)")
    for resource in data.get("result").get("resources"):
        match = pattern.match(resource["name"])
        if match is not None:
            index[int(match["year"])] = resource["id"]
    return index


def query_additional_eso_data(
    target_datetime: datetime, session: Session
) -> list[dict[str, Any]]:
    """Fetches embedded wind and solar and hydro storage data from the ESO API."""
    begin = (target_datetime - timedelta(days=2)).strftime("%Y-%m-%d")
    end = (target_datetime).strftime("%Y-%m-%d")
    if target_datetime > (datetime.now(tz=timezone.utc) - timedelta(days=30)):
        report_id = ESO_DEMAND_DATA_UPDATE_ID
    else:
        index = _create_eso_historical_demand_index(session)
        report_id = index[target_datetime.year]
    params = {
        "sql": f'''SELECT * FROM "{report_id}" WHERE "SETTLEMENT_DATE" BETWEEN '{begin}' AND '{end}' ORDER BY "SETTLEMENT_DATE"'''
    }
    response = session.get(ESO_NATIONAL_GRID_ENDPOINT, params=params)
    eso_data = response.json()["result"]["records"]
    return eso_data


def parse_eso_production(
    production_data: list[dict[str, Any]], logger: Logger
) -> ProductionBreakdownList:
    all_production_breakdowns: list[ProductionBreakdownList] = []
    for event in production_data:
        production_breakdown = ProductionBreakdownList(logger=logger)
        event_datetime = parse_datetime(
            event.get("SETTLEMENT_DATE"), event.get("SETTLEMENT_PERIOD")
        )
        production_mix = ProductionMix()
        storage_mix = StorageMix()
        for production_mode in ESO_FUEL_MAPPING:
            if ESO_FUEL_MAPPING[production_mode] == "hydro storage":
                storage_value = get_event_value(event, production_mode)
                if storage_value:
                    storage_mix.add_value("hydro", event.get(production_mode))
            else:
                production_value = get_event_value(event, production_mode)
                if production_value:
                    production_mix.add_value(
                        ESO_FUEL_MAPPING[production_mode],
                        event.get(production_mode),
                        correct_negative_with_zero=True,
                    )
        production_breakdown.append(
            zoneKey=ZoneKey("GB"),
            production=production_mix,
            storage=storage_mix,
            source=ESO_SOURCE,
            datetime=event_datetime,
        )

        all_production_breakdowns.append(production_breakdown)
    events = ProductionBreakdownList.merge_production_breakdowns(
        all_production_breakdowns, logger
    )
    return events


def parse_eso_hydro_storage(
    eso_data: list[dict[str, Any]], logger: Logger
) -> ProductionBreakdownList:
    """Parses only hydro storage data from the ESO API. This data will be merged with the B1620 data"""
    storage_breakdown = ProductionBreakdownList(logger=logger)
    for event in eso_data:
        event_datetime = parse_datetime(
            event.get("SETTLEMENT_DATE"), event.get("SETTLEMENT_PERIOD")
        )
        storage_mix = StorageMix()
        storage_value = get_event_value(event, "PUMP_STORAGE_PUMPING")
        storage_mix.add_value("hydro", storage_value)
        storage_breakdown.append(
            zoneKey=ZoneKey("GB"),
            storage=storage_mix,
            source=ESO_SOURCE,
            datetime=event_datetime,
        )
    return storage_breakdown


def query_production_fuelhh(
    session: Session, target_datetime: datetime, logger: Logger
) -> list[dict[str, Any]]:
    """Fetches production data from the FUELHH endpoint.
    This endpoint provides the half-hourly generation outturn (Generation By Fuel type)
    to give our users an indication of the generation outturn for Great Britain.
    The data is aggregated by Fuel Type category and updated at 30-minute intervals
    with average MW values over 30 minutes for each category."""
    params = {
        "settlementDateFrom": (target_datetime - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        ),
        "settlementDateTo": target_datetime.strftime("%Y-%m-%d"),
        "format": "json",
    }

    fuelhh_data = query_elexon(ELEXON_URLS["production_fuelhh"], session, params)

    return fuelhh_data if isinstance(fuelhh_data, list) else []


def query_and_merge_production_fuelhh_and_eso(
    session: Session, target_datetime: datetime, logger: Logger
) -> ProductionBreakdownList:
    events_fuelhh = query_production_fuelhh(session, target_datetime, logger)
    parsed_events_fuelhh = parse_production(events_fuelhh, logger, "FUELHH")
    events_eso = query_additional_eso_data(target_datetime, session)
    parsed_events_eso = parse_eso_production(events_eso, logger)

    merged_events = ProductionBreakdownList.merge_production_breakdowns(
        [parsed_events_fuelhh, parsed_events_eso], logger, matching_timestamps_only=True
    )
    return merged_events


# TODO: Why are we using this other endpoint instead of FUELINST that also have this data?
def query_exchange(
    zone_key: ZoneKey, session: Session, target_datetime: datetime, logger: Logger
) -> ExchangeList:
    all_exchanges: list[ExchangeList] = []
    for interconnector in ZONEKEY_TO_INTERCONNECTOR[zone_key]:
        exchange_params = {
            "settlementDateFrom": (target_datetime - timedelta(days=2)).strftime(
                "%Y-%m-%d"
            ),
            "settlementDateTo": target_datetime.strftime("%Y-%m-%d"),
            "interconnectorName": interconnector,
            "format": "json",
        }
        data = query_elexon(ELEXON_URLS["exchange"], session, exchange_params)
        exchange_data = data.get("data", []) if isinstance(data, dict) else []

        if EXHANGE_KEY_IS_IMPORT.get(zone_key):
            for event in exchange_data:
                event["generation"] = -1 * event["generation"]

        if not exchange_data:
            raise ParserException(
                parser="ELEXON.py",
                message=f"No exchange data found for {target_datetime.date()}",
            )
        for event in exchange_data:
            exchange_list = ExchangeList(logger)
            event_datetime_str = event.get("startTime")
            if event_datetime_str:
                event_datetime = datetime.fromisoformat(zulu_to_utc(event_datetime_str))
                exchange_list.append(
                    zoneKey=zone_key,
                    netFlow=event.get("generation"),
                    source=ELEXON_SOURCE,
                    datetime=event_datetime,
                )
            all_exchanges.append(exchange_list)
    return ExchangeList.merge_exchanges(all_exchanges, logger)


def query_actual_demand(
    session: Session, target_datetime: datetime, logger: Logger
) -> list[dict[str, Any]]:
    """Fetches actual electrical demand data from the ATL (Actual Total Load) endpoint."""
    params = {
        "publishDateTimeFrom": (target_datetime - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "publishDateTimeTo": target_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "format": "json",
    }

    demand_data = query_elexon(ELEXON_URLS["actual_load"], session, params)
    return demand_data if isinstance(demand_data, list) else []


def parse_demand_data(
    demand_data: list[dict[str, Any]], logger: Logger
) -> TotalConsumptionList:
    """Parses demand data from the ELEXON API."""
    consumption_list = TotalConsumptionList(logger=logger)

    for event in demand_data:
        event_datetime_str = event.get("startTime")
        consumption_value = get_event_value(
            event, "quantity"
        )  # or whatever the demand field is called

        if event_datetime_str and consumption_value is not None:
            event_datetime = datetime.fromisoformat(zulu_to_utc(event_datetime_str))
            consumption_list.append(
                zoneKey=ZoneKey("GB"),
                consumption=consumption_value,
                source=ELEXON_SOURCE,
                datetime=event_datetime,
            )
    return consumption_list


@refetch_frequency(timedelta(hours=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("GB"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    else:
        target_datetime = target_datetime.astimezone(timezone.utc)

    if target_datetime < ELEXON_START_DATE:
        raise ParserException(
            parser="ELEXON.py",
            message=f"Demand data is not available before {ELEXON_START_DATE.date()}",
        )
    demand_data = query_actual_demand(session, target_datetime, logger)
    parsed_demand = parse_demand_data(demand_data, logger)
    if not parsed_demand:
        raise ParserException(
            parser="ELEXON.py",
            message=f"No demand data found for {target_datetime.date()}",
        )
    return parsed_demand.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    session = session or Session()
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)

    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)

    exchangeKey = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    if target_datetime < ELEXON_START_DATE:
        raise ParserException(
            parser="ELEXON.py",
            message=f"Production data is not available before {ELEXON_START_DATE.date()}",
        )
    exchange_data = (
        query_exchange(exchangeKey, session, target_datetime, logger)
        if exchangeKey != "GB->IM"
        else query_IM_exchange(session, target_datetime, logger)
    )

    return exchange_data.to_list()


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("GB"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    else:
        target_datetime = target_datetime.astimezone(timezone.utc)

    if target_datetime < ELEXON_START_DATE:
        raise ParserException(
            parser="ELEXON.py",
            message=f"Production data is not available before {ELEXON_START_DATE.date()}",
        )

    data = query_and_merge_production_fuelhh_and_eso(session, target_datetime, logger)
    eso_data = query_additional_eso_data(target_datetime, session)
    parsed_hydro_storage_data = parse_eso_hydro_storage(eso_data, logger)

    return ProductionBreakdownList.merge_production_breakdowns(
        [data, parsed_hydro_storage_data],
        logger,
        matching_timestamps_only=True,
    ).to_list()


def validate_bmrs_data(data: ProductionBreakdownList):
    """Check if the PowerProductionBreakdown event contains a full power breakdown or just wind and solar or if data is missing."""
    if not data:
        return False
    available_production_modes = []
    for event in data.to_list():
        available_production_modes += [*event["production"].keys()]
    return "gas" in set(available_production_modes)
