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
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

ELEXON_API_ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1"
ELEXON_URLS = {
    "production": "/".join((ELEXON_API_ENDPOINT, "datasets/AGPT/stream")),
    "production_fuelhh": "/".join((ELEXON_API_ENDPOINT, "datasets/FUELHH/stream")),
    "exchange": "/".join((ELEXON_API_ENDPOINT, "generation/outturn/interconnectors")),
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
    "INTFR": "exchange",
    "INTIRL": "exchange",
    "INTNED": "exchange",
    "INTEW": "exchange",
    "BIOMASS": "biomass",
    "INTNEM": "exchange",
    "INTELEC": "exchange",
    "INTIFA2": "exchange",
    "INTNSL": "exchange",
    "INTVKL": "exchange",
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
    "GB->IE": ["Ireland(East-West)"],
    "GB->NL": ["Netherlands(BritNed)"],
    "GB->NO-NO2": ["North Sea Link (INTNSL)"],
}


def query_elexon(url: str, session: Session, params: dict) -> list:
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


def query_production(
    session: Session, target_datetime: datetime, logger: Logger
) -> ProductionBreakdownList:
    """Fetches production data from the B1620 endpoint from the ELEXON API."""
    production_params = {
        "publishDateTimeFrom": (target_datetime - timedelta(days=2)).strftime(
            "%Y-%m-%d 00:00"
        ),
        "publishDateTimeTo": target_datetime.strftime("%Y-%m-%d %H:%M"),
    }
    production_data = query_elexon(
        ELEXON_URLS["production"], session, production_params
    )

    parsed_events = parse_production(production_data, logger, "B1620")
    return parsed_events


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
        event_datetime = parse_datetime(
            event.get("settlementDate"), event.get("settlementPeriod")
        )
        production_mix = ProductionMix()
        storage_mix = StorageMix()

        production_mode = mode_mapping[event.get(mode_key)]

        if production_mode == "exchange":
            continue

        if production_mode == "hydro storage":
            storage_value = get_event_value(event, quantity_key)
            if storage_value:
                storage_mix.add_value("hydro", -1 * storage_value)
                production_breakdown.append(
                    zoneKey=ZoneKey("GB"),
                    storage=storage_mix,
                    source=ELEXON_SOURCE,
                    datetime=event_datetime,
                )
        else:
            production_value = get_event_value(event, quantity_key)
            if production_value:
                production_mix.add_value(
                    production_mode, production_value, correct_negative_with_zero=True
                )
                production_breakdown.append(
                    zoneKey=ZoneKey("GB"),
                    production=production_mix,
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
                    production_breakdown.append(
                        zoneKey=ZoneKey("GB"),
                        storage=storage_mix,
                        source=ESO_SOURCE,
                        datetime=event_datetime,
                    )
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
        if storage_value:
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
    return fuelhh_data


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
        exchange_data = query_elexon(
            ELEXON_URLS["exchange"], session, exchange_params
        ).get("data")

        if not exchange_data:
            raise ParserException(
                parser="ELEXON.py",
                message=f"No exchange data found for {target_datetime.date()}",
            )
        for event in exchange_data:
            exchange_list = ExchangeList(logger)
            event_datetime = parse_datetime(
                event.get("settlementDate"), event.get("settlementPeriod")
            )

            exchange_list.append(
                zoneKey=zone_key,
                netFlow=event.get("generation"),
                source=ELEXON_SOURCE,
                datetime=event_datetime,
            )
            all_exchanges.append(exchange_list)
    return ExchangeList.merge_exchanges(all_exchanges, logger)


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

    exchangeKey = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    if target_datetime < ELEXON_START_DATE:
        raise ParserException(
            parser="ELEXON.py",
            message=f"Production data is not available before {ELEXON_START_DATE.date()}",
        )
    exchange_data = query_exchange(exchangeKey, session, target_datetime, logger)

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

    data_b1620 = query_production(session, target_datetime, logger)

    if not validate_bmrs_data(data_b1620):
        data = query_and_merge_production_fuelhh_and_eso(
            session, target_datetime, logger
        )
    else:
        # add hydro pumping data from ESO (B1620 only includes pumped storage production (injected on the grid) and not the pumping (withdrawn from the grid)
        eso_data = query_additional_eso_data(target_datetime, session)
        parsed_hydro_storage_data = parse_eso_hydro_storage(eso_data, logger)
        data = ProductionBreakdownList.merge_production_breakdowns(
            [data_b1620, parsed_hydro_storage_data],
            logger,
            matching_timestamps_only=True,
        )
    return data.to_list()


def validate_bmrs_data(data: ProductionBreakdownList):
    """Check if the PowerProductionBreakdown event contains a full power breakdown or just wind and solar or if data is missing."""
    if not data:
        return False
    available_production_modes = []
    for event in data.to_list():
        available_production_modes += [*event["production"].keys()]
    if "gas" not in set(available_production_modes):
        return False
    return True
