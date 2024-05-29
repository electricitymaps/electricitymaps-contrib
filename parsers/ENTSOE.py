#!/usr/bin/env python3

"""
Parser that uses the ENTSOE API to return the following data types.

Consumption
Production
Exchanges
Exchange Forecast
Day-ahead Price
Generation Forecast
Consumption Forecast

Link to the API documentation:
https://documenter.getpostman.com/view/7009892/2s93JtP3F6
"""

import itertools
import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import lru_cache
from logging import Logger, getLogger
from operator import itemgetter
from typing import Any

import numpy as np
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from parsers.lib.config import refetch_frequency

from .lib.exceptions import ParserException
from .lib.utils import get_token
from .lib.validation import validate

SOURCE = "entsoe.eu"

ENTSOE_URL = "https://entsoe-proxy-jfnx5klx2a-ew.a.run.app"

DEFAULT_LOOKBACK_HOURS_REALTIME = 72
DEFAULT_TARGET_HOURS_REALTIME = (-DEFAULT_LOOKBACK_HOURS_REALTIME, 0)
DEFAULT_TARGET_HOURS_FORECAST = (-24, 48)


class WindAndSolarProductionForecastTypes(Enum):
    DAY_AHEAD = "A01"
    INTRADAY = "A40"
    CURRENT = "A18"


# The order of the forecast types is important for the parser to use the most recent data
# This ensures that the order is consistent across all runs even if the enum is changed
ORDERED_FORECAST_TYPES = [
    WindAndSolarProductionForecastTypes.DAY_AHEAD,
    WindAndSolarProductionForecastTypes.INTRADAY,
    WindAndSolarProductionForecastTypes.CURRENT,
]

ENTSOE_PARAMETER_DESC = {
    "B01": "Biomass",
    "B02": "Fossil Brown coal/Lignite",
    "B03": "Fossil Coal-derived gas",
    "B04": "Fossil Gas",
    "B05": "Fossil Hard coal",
    "B06": "Fossil Oil",
    "B07": "Fossil Oil shale",
    "B08": "Fossil Peat",
    "B09": "Geothermal",
    "B10": "Hydro Pumped Storage",
    "B11": "Hydro Run-of-river and poundage",
    "B12": "Hydro Water Reservoir",
    "B13": "Marine",
    "B14": "Nuclear",
    "B15": "Other renewable",
    "B16": "Solar",
    "B17": "Waste",
    "B18": "Wind Offshore",
    "B19": "Wind Onshore",
    "B20": "Other",
}
ENTSOE_PARAMETER_BY_DESC = {v: k for k, v in ENTSOE_PARAMETER_DESC.items()}
ENTSOE_PARAMETER_GROUPS = {
    "production": {
        "biomass": ["B01", "B17"],
        "coal": ["B02", "B05", "B07", "B08"],
        "gas": ["B03", "B04"],
        "geothermal": ["B09"],
        "hydro": ["B11", "B12"],
        "nuclear": ["B14"],
        "oil": ["B06"],
        "solar": ["B16"],
        "wind": ["B18", "B19"],
        "unknown": ["B20", "B13", "B15"],
    },
    "storage": {"hydro": ["B10"]},
}
# ENTSOE production type codes mapped to their Electricity Maps production type.
ENTSOE_PARAMETER_BY_GROUP = {
    ENTSOE_key: data_type
    for key in ["production", "storage"]
    for data_type, groups in ENTSOE_PARAMETER_GROUPS[key].items()
    for ENTSOE_key in groups
}

# Get all the individual storage parameters in one list
ENTSOE_STORAGE_PARAMETERS = list(
    itertools.chain.from_iterable(ENTSOE_PARAMETER_GROUPS["storage"].values())
)
# Define all ENTSOE zone_key <-> domain mapping
# see https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
ENTSOE_DOMAIN_MAPPINGS: dict[str, str] = {
    "AL": "10YAL-KESH-----5",
    "AT": "10YAT-APG------L",
    "AZ": "10Y1001A1001B05V",
    "BA": "10YBA-JPCC-----D",
    "BE": "10YBE----------2",
    "BG": "10YCA-BULGARIA-R",
    "BY": "10Y1001A1001A51S",
    "CH": "10YCH-SWISSGRIDZ",
    "CZ": "10YCZ-CEPS-----N",
    "DE": "10Y1001A1001A83F",
    "DE-LU": "10Y1001A1001A82H",
    "DK": "10Y1001A1001A65H",
    "DK-DK1": "10YDK-1--------W",
    "DK-DK2": "10YDK-2--------M",
    "EE": "10Y1001A1001A39I",
    "ES": "10YES-REE------0",
    "FI": "10YFI-1--------U",
    "FR": "10YFR-RTE------C",
    "GB": "10YGB----------A",
    "GB-NIR": "10Y1001A1001A016",
    "GE": "10Y1001A1001B012",
    "GR": "10YGR-HTSO-----Y",
    "HR": "10YHR-HEP------M",
    "HU": "10YHU-MAVIR----U",
    "IE": "10YIE-1001A00010",
    "IE(SEM)": "10Y1001A1001A59C",
    "IT": "10YIT-GRTN-----B",
    "IT-BR": "10Y1001A1001A699",
    "IT-CA": "10Y1001C--00096J",
    "IT-CNO": "10Y1001A1001A70O",
    "IT-CSO": "10Y1001A1001A71M",
    "IT-FO": "10Y1001A1001A72K",
    "IT-NO": "10Y1001A1001A73I",
    "IT-PR": "10Y1001A1001A76C",
    "IT-SACOAC": "10Y1001A1001A885",
    "IT-SACODC": "10Y1001A1001A893",
    "IT-SAR": "10Y1001A1001A74G",
    "IT-SIC": "10Y1001A1001A75E",
    "IT-SO": "10Y1001A1001A788",
    "LT": "10YLT-1001A0008Q",
    "LU": "10YLU-CEGEDEL-NQ",
    "LV": "10YLV-1001A00074",
    "MD": "10Y1001A1001A990",
    "ME": "10YCS-CG-TSO---S",
    "MK": "10YMK-MEPSO----8",
    "MT": "10Y1001A1001A93C",
    "NL": "10YNL----------L",
    "NO": "10YNO-0--------C",
    "NO-NO1": "10YNO-1--------2",
    "NO-NO2": "10YNO-2--------T",
    "NO-NO3": "10YNO-3--------J",
    "NO-NO4": "10YNO-4--------9",
    "NO-NO5": "10Y1001A1001A48H",
    "PL": "10YPL-AREA-----S",
    "PT": "10YPT-REN------W",
    "RO": "10YRO-TEL------P",
    "RS": "10YCS-SERBIATSOV",
    "RU": "10Y1001A1001A49F",
    "RU-KGD": "10Y1001A1001A50U",
    "SE": "10YSE-1--------K",
    "SE-SE1": "10Y1001A1001A44P",
    "SE-SE2": "10Y1001A1001A45N",
    "SE-SE3": "10Y1001A1001A46L",
    "SE-SE4": "10Y1001A1001A47J",
    "SI": "10YSI-ELES-----O",
    "SK": "10YSK-SEPS-----K",
    "TR": "10YTR-TEIAS----W",
    "UA": "10YUA-WEPS-----0",
    "UA-IPS": "10Y1001C--000182",
    "XK": "10Y1001C--00100H",
}

# Generation per unit can only be obtained at EIC (Control Area) level
ENTSOE_EIC_MAPPING: dict[str, str] = {
    "DK-DK1": "10Y1001A1001A796",
    "DK-DK2": "10Y1001A1001A796",
    "FI": "10YFI-1--------U",
    "PL": "10YPL-AREA-----S",
    "SE-SE1": "10YSE-1--------K",
    "SE-SE2": "10YSE-1--------K",
    "SE-SE3": "10YSE-1--------K",
    "SE-SE4": "10YSE-1--------K",
    # TODO: ADD DE
}

# Define zone_keys to an array of zone_keys for aggregated production data
ZONE_KEY_AGGREGATES: dict[str, list[str]] = {
    "IT-SO": ["IT-CA", "IT-SO"],
}

# Some exchanges require specific domains
ENTSOE_EXCHANGE_DOMAIN_OVERRIDE: dict[str, list[str]] = {
    "AT->IT-NO": [ENTSOE_DOMAIN_MAPPINGS["AT"], ENTSOE_DOMAIN_MAPPINGS["IT"]],
    "BY->UA": [ENTSOE_DOMAIN_MAPPINGS["BY"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
    "DE->DK-DK1": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["DK-DK1"]],
    "DE->DK-DK2": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["DK-DK2"]],
    "DE->NO-NO2": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["NO-NO2"]],
    "DE->SE-SE4": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["SE-SE4"]],
    "EE->RU-1": [ENTSOE_DOMAIN_MAPPINGS["EE"], ENTSOE_DOMAIN_MAPPINGS["RU"]],
    "FI->RU-1": [ENTSOE_DOMAIN_MAPPINGS["FI"], ENTSOE_DOMAIN_MAPPINGS["RU"]],
    "FR-COR->IT-CNO": [
        ENTSOE_DOMAIN_MAPPINGS["IT-SACODC"],
        ENTSOE_DOMAIN_MAPPINGS["IT-CNO"],
    ],
    "GE->RU-1": [ENTSOE_DOMAIN_MAPPINGS["GE"], ENTSOE_DOMAIN_MAPPINGS["RU"]],
    "GR->IT-SO": [ENTSOE_DOMAIN_MAPPINGS["GR"], ENTSOE_DOMAIN_MAPPINGS["IT-SO"]],
    "HU->UA": [ENTSOE_DOMAIN_MAPPINGS["HU"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
    "IT-CSO->ME": [ENTSOE_DOMAIN_MAPPINGS["IT"], ENTSOE_DOMAIN_MAPPINGS["ME"]],
    "IT-SIC->IT-SO": [
        ENTSOE_DOMAIN_MAPPINGS["IT-SIC"],
        ENTSOE_DOMAIN_MAPPINGS["IT-CA"],
    ],
    "LV->RU-1": [ENTSOE_DOMAIN_MAPPINGS["LV"], ENTSOE_DOMAIN_MAPPINGS["RU"]],
    "MD->UA": [ENTSOE_DOMAIN_MAPPINGS["MD"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
    "PL->UA": [ENTSOE_DOMAIN_MAPPINGS["PL"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
    "RO->UA": [ENTSOE_DOMAIN_MAPPINGS["RO"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
    "RU-1->UA": [ENTSOE_DOMAIN_MAPPINGS["RU"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
    "SK->UA": [ENTSOE_DOMAIN_MAPPINGS["SK"], ENTSOE_DOMAIN_MAPPINGS["UA-IPS"]],
}

EXCHANGE_AGGREGATES: dict[str, list[list]] = {
    "FR-COR->IT-SAR": [
        [ENTSOE_DOMAIN_MAPPINGS["IT-SACOAC"], ENTSOE_DOMAIN_MAPPINGS["IT-SAR"]],
        [ENTSOE_DOMAIN_MAPPINGS["IT-SACODC"], ENTSOE_DOMAIN_MAPPINGS["IT-SAR"]],
    ],
}

# Some zone_keys are part of bidding zone domains for price data
ENTSOE_PRICE_DOMAIN_MAPPINGS: dict[str, str] = {
    **ENTSOE_DOMAIN_MAPPINGS,  # Note: This has to be first so the domains are overwritten.
    "AX": ENTSOE_DOMAIN_MAPPINGS["SE-SE3"],
    "DK-BHM": ENTSOE_DOMAIN_MAPPINGS["DK-DK2"],
    "DE": ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
    "IE": ENTSOE_DOMAIN_MAPPINGS["IE(SEM)"],
    "GB-NIR": ENTSOE_DOMAIN_MAPPINGS["IE(SEM)"],
    "LU": ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
}

ENTSOE_UNITS_TO_ZONE: dict[str, str] = {
    # DK-DK1
    "Anholt": "DK-DK1",
    "Esbjergvaerket 3": "DK-DK1",
    "Fynsvaerket 7": "DK-DK1",
    "Horns Rev A": "DK-DK1",
    "Horns Rev B": "DK-DK1",
    "Nordjyllandsvaerket 3": "DK-DK1",
    "Silkeborgvaerket": "DK-DK1",
    "Skaerbaekvaerket 3": "DK-DK1",
    "Studstrupvaerket 3": "DK-DK1",
    "Studstrupvaerket 4": "DK-DK1",
    # DK-DK2
    "Amagervaerket 3": "DK-DK2",
    "Asnaesvaerket 2": "DK-DK2",
    "Asnaesvaerket 5": "DK-DK2",
    "Avedoerevaerket 1": "DK-DK2",
    "Avedoerevaerket 2": "DK-DK2",
    "Kyndbyvaerket 21": "DK-DK2",
    "Kyndbyvaerket 22": "DK-DK2",
    "Roedsand 1": "DK-DK2",
    "Roedsand 2": "DK-DK2",
    # FI
    "Alholmens B2": "FI",
    "Haapavesi B1": "FI",
    "Kaukaan Voima G10": "FI",
    "Keljonlahti B1": "FI",
    "Loviisa 1 G11": "FI",
    "Loviisa 1 G12": "FI",
    "Loviisa 2 G21": "FI",
    "Loviisa 2 G22": "FI",
    "Olkiluoto 1 B1": "FI",
    "Olkiluoto 2 B2": "FI",
    "Toppila B2": "FI",
    # SE-SE1
    "Bastusel G1": "SE-SE1",
    "Gallejaur G1": "SE-SE1",
    "Gallejaur G2": "SE-SE1",
    "Harsprånget G1": "SE-SE1",
    "Harsprånget G2": "SE-SE1",
    "Harsprånget G4": "SE-SE1",
    "Harsprånget G5": "SE-SE1",
    "Letsi G1": "SE-SE1",
    "Letsi G2": "SE-SE1",
    "Letsi G3": "SE-SE1",
    "Ligga G3": "SE-SE1",
    "Messaure G1": "SE-SE1",
    "Messaure G2": "SE-SE1",
    "Messaure G3": "SE-SE1",
    "Porjus G11": "SE-SE1",
    "Porjus G12": "SE-SE1",
    "Porsi G3": "SE-SE1",
    "Ritsem G1": "SE-SE1",
    "Seitevare G1": "SE-SE1",
    "Vietas G1": "SE-SE1",
    "Vietas G2": "SE-SE1",
    # SE-SE2
    "Stalon G1": "SE-SE2",
    "Stornorrfors G1": "SE-SE2",
    "Stornorrfors G2": "SE-SE2",
    "Stornorrfors G3": "SE-SE2",
    "Stornorrfors G4": "SE-SE2",
    # SE-SE3
    "Forsmark block 1 G11": "SE-SE3",
    "Forsmark block 1 G12": "SE-SE3",
    "Forsmark block 2 G21": "SE-SE3",
    "Forsmark block 2 G22": "SE-SE3",
    "Forsmark block 3 G31": "SE-SE3",
    "KVV Västerås G3": "SE-SE3",
    "KVV1 Värtaverket": "SE-SE3",
    "KVV6 Värtaverket": "SE-SE3",
    "KVV8 Värtaverket": "SE-SE3",
    "Oskarshamn G3": "SE-SE3",
    "Oskarshamn G1Ö+G1V": "SE-SE3",
    "Ringhals block 1 G11": "SE-SE3",
    "Ringhals block 1 G12": "SE-SE3",
    "Ringhals block 2 G21": "SE-SE3",
    "Ringhals block 2 G22": "SE-SE3",
    "Ringhals block 3 G31": "SE-SE3",
    "Ringhals block 3 G32": "SE-SE3",
    "Ringhals block 4 G41": "SE-SE3",
    "Ringhals block 4 G42": "SE-SE3",
    "Rya KVV": "SE-SE3",
    "Stenungsund B3": "SE-SE3",
    "Stenungsund B4": "SE-SE3",
    "Trängslet G1": "SE-SE3",
    "Trängslet G2": "SE-SE3",
    "Trängslet G3": "SE-SE3",
    "Uppsala KVV": "SE-SE3",
    "Åbyverket Örebro": "SE-SE3",
    # SE-SE4
    "Gasturbiner Halmstad G12": "SE-SE4",
    "Karlshamn G1": "SE-SE4",
    "Karlshamn G2": "SE-SE4",
    "Karlshamn G3": "SE-SE4",
}

VALIDATIONS: dict[str, dict[str, Any]] = {
    # This is a list of criteria to ensure validity of data,
    # used in validate_production()
    # Note that "required" means data is present in ENTSOE.
    # It will still work if data is present but 0.
    # "expected_range" and "floor" only count production and storage
    # - not exchanges!
    "BA": {"expected_range": (500, 6500)},
    "BE": {
        "expected_range": (3000, 25000),
    },
    "BG": {
        "expected_range": (2000, 20000),
    },
    "CH": {
        "expected_range": (2000, 25000),
    },
    "CZ": {
        # usual load is in 7-12 GW range
        "expected_range": (3000, 25000),
    },
    "DE": {
        # Germany sometimes has problems with categories of generation missing from ENTSOE.
        # Normally there is constant production of a few GW from hydro and biomass
        # and when those are missing this can indicate that others are missing as well.
        # We have also never seen unknown being 0.
        # Usual load is in 30 to 80 GW range.
        "expected_range": (20000, 100000),
    },
    "ES": {
        "expected_range": (10000, 80000),
    },
    "FI": {
        "expected_range": (2000, 20000),
    },
    "GB": {
        "expected_range": (10000, 80000),
    },
    "GR": {
        "expected_range": (2000, 20000),
    },
    "IE": {
        "expected_range": (1000, 15000),
    },
    "IT": {
        "expected_range": (5000, 50000),
    },
    "PL": {
        # usual load is in 10-20 GW range
        "expected_range": (5000, 35000),
    },
    "PT": {
        "expected_range": (1000, 20000),
    },
    "RO": {
        "expected_range": (2000, 25000),
    },
    "RS": {
        "expected_range": {
            "coal": (
                800,
                7000,
            ),  # 7 GW is 1 GW more than the production capacity of Serbia.
            "hydro": (0, 5000),  # 5 GW is double the production capacity of Serbia.
        },
    },
    "SI": {
        # own total generation capacity is around 4 GW
        "expected_range": (140, 5000),
    },
}


def closest_in_time_key(x, target_datetime: datetime | None, datetime_key="datetime"):
    if target_datetime is None:
        target_datetime = datetime.now(timezone.utc)
    if isinstance(target_datetime, datetime):
        return np.abs((x[datetime_key] - target_datetime).seconds)


def query_ENTSOE(
    session: Session,
    params: dict[str, str],
    span: tuple,
    target_datetime: datetime | None = None,
    function_name: str = "",
) -> str:
    """
    Makes a standard query to the ENTSOE API with a modifiable set of parameters.
    Allows an existing session to be passed.
    Raises an exception if no API token is found.
    Returns a request object.
    """
    if target_datetime is None:
        target_datetime = datetime.now(timezone.utc)

    if not isinstance(target_datetime, datetime):
        raise ParserException(
            parser="ENTSOE.py",
            message="target_datetime has to be a datetime in query_entsoe",
        )

    params["periodStart"] = (target_datetime + timedelta(hours=span[0])).strftime(
        "%Y%m%d%H00"  # YYYYMMDDHH00
    )
    params["periodEnd"] = (target_datetime + timedelta(hours=span[1])).strftime(
        "%Y%m%d%H00"  # YYYYMMDDHH00
    )

    token = get_token("ENTSOE_TOKEN")
    params["securityToken"] = token
    response: Response = session.get(ENTSOE_URL, params=params)
    if response.ok:
        return response.text

    # If we get here, the request failed to fetch valid data
    # and we will check the response for an error message
    exception_message = None
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.find_all("text")
    if len(text):
        error_text = soup.find_all("text")[0].prettify()
        if "No matching data found" in error_text:
            exception_message = "No matching data found"
    if exception_message is None:
        exception_message = (
            f"Status code: [{response.status_code}]. Reason: {response.reason}"
        )

    raise ParserException(
        parser="ENTSOE.py",
        message=exception_message
        if exception_message
        else "An unknown error occured while querying ENTSOE.",
    )


def query_consumption(
    domain: str, session: Session, target_datetime: datetime | None = None
) -> str | None:
    params = {
        "documentType": "A65",
        "processType": "A16",
        "outBiddingZone_Domain": domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_REALTIME,
        function_name=query_consumption.__name__,
    )


def query_production(
    in_domain: str, session: Session, target_datetime: datetime | None = None
) -> str | None:
    params = {
        "documentType": "A75",
        "processType": "A16",  # Realised
        "in_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_REALTIME,
        function_name=query_production.__name__,
    )


def query_production_per_units(
    psr_type: str,
    domain: str,
    session: Session,
    target_datetime: datetime | None = None,
) -> str | None:
    params = {
        "documentType": "A73",
        "processType": "A16",
        "psrType": psr_type,
        "in_Domain": domain,
    }
    # Note: ENTSOE only supports 1d queries for this type
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=(-24, 0),
        function_name=query_production_per_units.__name__,
    )


def query_exchange(
    in_domain: str,
    out_domain: str,
    session: Session,
    target_datetime: datetime | None = None,
) -> str | None:
    params = {
        "documentType": "A11",
        "in_Domain": in_domain,
        "out_Domain": out_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_REALTIME,
        function_name=query_exchange.__name__,
    )


def query_exchange_forecast(
    in_domain: str,
    out_domain: str,
    session: Session,
    target_datetime: datetime | None = None,
) -> str | None:
    """Gets exchange forecast for 48 hours ahead and previous 24 hours."""

    params = {
        "documentType": "A09",  # Finalised schedule
        "in_Domain": in_domain,
        "out_Domain": out_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_FORECAST,
        function_name=query_exchange_forecast.__name__,
    )


def query_price(
    domain: str, session: Session, target_datetime: datetime | None = None
) -> str | None:
    """Gets day-ahead price for 24 hours ahead and previous 72 hours."""

    params = {
        "documentType": "A44",
        "in_Domain": domain,
        "out_Domain": domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=(-DEFAULT_LOOKBACK_HOURS_REALTIME, 24),
        function_name=query_price.__name__,
    )


def query_generation_forecast(
    in_domain: str, session: Session, target_datetime: datetime | None = None
) -> str | None:
    """Gets generation forecast for 48 hours ahead and previous 24 hours."""

    # Note: this does not give a breakdown of the production
    params = {
        "documentType": "A71",  # Generation Forecast
        "processType": "A01",  # Realised
        "in_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_FORECAST,
        function_name=query_generation_forecast.__name__,
    )


def query_consumption_forecast(
    in_domain: str, session: Session, target_datetime: datetime | None = None
) -> str | None:
    """Gets consumption forecast for 48 hours ahead and previous 24 hours."""

    params = {
        "documentType": "A65",  # Load Forecast
        "processType": "A01",
        "outBiddingZone_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_FORECAST,
        function_name=query_consumption_forecast.__name__,
    )


def query_wind_solar_production_forecast(
    in_domain: str,
    session: Session,
    data_type: WindAndSolarProductionForecastTypes,
    target_datetime: datetime | None = None,
) -> str | None:
    """Gets consumption forecast for 48 hours ahead and previous 24 hours."""

    params = {
        "documentType": "A69",  # Forecast
        "processType": WindAndSolarProductionForecastTypes(data_type).value,
        "in_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=DEFAULT_TARGET_HOURS_FORECAST,
        function_name=query_wind_solar_production_forecast.__name__,
    )


# TODO: Remove this when we run on Python 3.11 or above
@lru_cache(maxsize=8)
def zulu_to_utc(datetime_string: str) -> str:
    """Converts a zulu time string to a UTC time string."""
    return datetime_string.replace("Z", "+00:00")


@lru_cache(maxsize=1024)
def datetime_from_position(start: datetime, position: int, resolution: str) -> datetime:
    """Finds time granularity of data."""

    m = re.search(r"PT(\d+)([M])", resolution)
    if m is not None:
        digits = int(m.group(1))
        scale = m.group(2)
        if scale == "M":
            return start + timedelta(minutes=(position - 1) * digits)
    raise NotImplementedError(f"Could not recognise resolution {resolution}")


def parse_scalar(
    xml_text: str,
    only_inBiddingZone_Domain: bool = False,
    only_outBiddingZone_Domain: bool = False,
) -> list[tuple[float, datetime]] | None:
    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    values: list[float] = []
    datetimes: list[datetime] = []
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start = datetime.fromisoformat(
            zulu_to_utc(timeseries.find_all("start")[0].contents[0])
        )
        if (
            only_inBiddingZone_Domain
            and not timeseries.find("inBiddingZone_Domain.mRID".lower())
        ) or (
            only_outBiddingZone_Domain
            and not timeseries.find("outBiddingZone_Domain.mRID".lower())
        ):
            continue
        for entry in timeseries.find_all("point"):
            position = int(entry.find("position").contents[0])
            value = float(entry.find("quantity").contents[0])
            dt = datetime_from_position(datetime_start, position, resolution)
            values.append(value)
            datetimes.append(dt)

    return list(zip(values, datetimes, strict=True))


def parse_production(
    xml: str,
    logger: Logger,
    zoneKey: ZoneKey,
    forecasted: bool = False,
) -> ProductionBreakdownList:
    production_breakdowns = ProductionBreakdownList(logger)
    source_type = EventSourceType.forecasted if forecasted else EventSourceType.measured
    if not xml:
        return production_breakdowns
    soup = BeautifulSoup(xml, "html.parser")
    list_of_raw_data = _get_raw_production_events(soup)

    grouped_data = _group_production_data_by_datetime(list_of_raw_data)

    expected_length = _get_expected_production_group_length(grouped_data)

    # Loop over the grouped data and create production and storage mixes for each datetime.
    for dt, values in grouped_data.items():
        production, storage = _create_production_and_storage_mixes(
            zoneKey, dt, values, expected_length, logger
        )
        # If production and storage are None, the datapoint is considered invalid and is skipped
        # in order to not crash the parser.
        if production is None and storage is None:
            continue

        production_breakdowns.append(
            zoneKey=zoneKey,
            datetime=dt,
            source=SOURCE,
            sourceType=source_type,
            production=production,
            storage=storage,
        )

    return production_breakdowns


def _get_raw_production_events(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """
    Extracts the raw production events from the soup object and returns a list of dictionaries containing the raw production events.
    """
    list_of_raw_data = []
    # Each timeserie is dedicated to a different fuel type.
    for timeseries in soup.find_all("timeseries"):
        # The resolution is the time between each point in the timeseries.
        resolution = str(timeseries.find("resolution").contents[0])
        # The start time of the timeseries.
        datetime_start = datetime.fromisoformat(
            zulu_to_utc(timeseries.find("start").contents[0])
        )
        # The fuel code is the ENTSOE code for the fuel type.
        fuel_code = str(timeseries.find("mktpsrtype").find("psrtype").contents[0])
        # Loop over all the points in the timeseries.
        for entry in timeseries.find_all("point"):
            # The quantity is the amount of energy produced or consumed at the given position.
            quantity = float(entry.find("quantity").contents[0])
            # The position is the index of the point in the timeseries.
            position = int(entry.find("position").contents[0])
            # Since all values in ENTSOE are positive, we need to check if
            # the value is production or consumption so we can set the quantity
            # to a negative value if it is consumption.
            is_production = bool(timeseries.find("inBiddingZone_Domain.mRID".lower()))
            # Calculate the datetime of the point based on the start time and the position.
            dt = datetime_from_position(datetime_start, position, resolution)
            # Appends the raw data to a master list so it later can be sorted and grouped by datetime.
            list_of_raw_data.append(
                {
                    "datetime": dt,
                    "fuel_code": fuel_code,
                    "quantity": quantity if is_production else -quantity,
                }
            )

    return list_of_raw_data


def _create_production_and_storage_mixes(
    zoneKey: ZoneKey,
    dt: datetime,
    values: list[dict[str, Any]],
    expected_length: int,
    logger: Logger,
) -> tuple[ProductionMix, StorageMix] | tuple[None, None]:
    """
    Creates a populated ProductionMix and StorageMix object from a list of production values and ensures that the expected length is met.
    If the expected length is not met, the datapoint is discarded. And the function returns (None, None).
    """
    value_length = len(values)
    # Checks that the number of values have the expected length and skips the datapoint if not.
    if value_length < expected_length:
        if zoneKey == "BE" and value_length == expected_length - 1:
            logger.warning(
                f"BE only has {value_length} production values for {dt}, but should have {expected_length}. BE doesn't report 0 values for storage so we will continue."
            )
        else:
            logger.warning(
                f"Expected {expected_length} production values for {dt}, received {value_length} instead. Discarding datapoint..."
            )
            return None, None
    production = ProductionMix()
    storage = StorageMix()
    for production_mode in values:
        _datetime, fuel_code, quantity = production_mode.values()
        fuel_em_type = ENTSOE_PARAMETER_BY_GROUP[fuel_code]
        if fuel_code in ENTSOE_STORAGE_PARAMETERS:
            storage.add_value(fuel_em_type, -quantity)
        else:
            production.add_value(
                fuel_em_type, quantity, correct_negative_with_zero=True
            )

    return production, storage


def _get_expected_production_group_length(
    grouped_data: dict[datetime, list[dict[str, Any]]],
) -> int:
    """
    Returns the expected length of the grouped data. This is the maximum length of the grouped data values.
    """
    expected_length = 0
    if grouped_data:
        expected_length = max(len(v) for v in grouped_data.values())
    return expected_length


def _group_production_data_by_datetime(
    list_of_raw_data,
) -> dict[datetime, list[dict[str, Any]]]:
    """
    Sorts and groups raw production objects in the format of `{datetime: datetime.datetime, fuel_code: str, quantity: float}` by the datetime key.
    And returns a dictionary with the datetime as the key and a list of the grouped data as the value.
    """
    # Sort the data in place by the datetime key so we can group it by datetime.
    list_of_raw_data.sort(key=itemgetter("datetime"))
    # Group the data by the datetime key. It requires the data to be sorted by the datetime key first.
    grouped_data = {
        k: list(v)
        for k, v in itertools.groupby(list_of_raw_data, key=itemgetter("datetime"))
    }

    return grouped_data


def parse_production_per_units(xml_text: str) -> Any | None:
    values = {}

    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find("resolution").contents[0])
        datetime_start = datetime.fromisoformat(
            zulu_to_utc(timeseries.find("start").contents[0])
        )
        is_production = bool(timeseries.find("inBiddingZone_Domain.mRID".lower()))
        psr_type = str(timeseries.find("mktpsrtype").find("psrtype").contents[0])
        unit_key = str(
            timeseries.find("mktpsrtype")
            .find("powersystemresources")
            .find("mrid")
            .contents[0]
        )
        unit_name = str(
            timeseries.find("mktpsrtype")
            .find("powersystemresources")
            .find("name")
            .contents[0]
        )
        if not is_production:
            continue
        for entry in timeseries.find_all("point"):
            quantity = float(entry.find("quantity").contents[0])
            position = int(entry.find("position").contents[0])
            dt = datetime_from_position(datetime_start, position, resolution)
            key = (unit_key, dt)
            if key in values:
                if is_production:
                    values[key]["production"] += quantity
                else:
                    values[key]["production"] -= quantity
            else:
                values[key] = {
                    "datetime": dt,
                    "production": quantity,
                    "productionType": ENTSOE_PARAMETER_BY_GROUP[psr_type],
                    "unitKey": unit_key,
                    "unitName": unit_name,
                }

    return values.values()


def parse_exchange(
    xml_text: str,
    is_import: bool,
    sorted_zone_keys: ZoneKey,
    logger: Logger,
    is_forecast: bool = False,
) -> ExchangeList:
    exchange_list = ExchangeList(logger)

    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find("resolution").contents[0])
        datetime_start = datetime.fromisoformat(
            zulu_to_utc(timeseries.find("start").contents[0])
        )
        # Only use contract_marketagreement.type == A01 (Total to avoid double counting some columns)
        if (
            timeseries.find("contract_marketagreement.type")
            and timeseries.find("contract_marketagreement.type").contents[0] != "A05"
        ):
            continue

        for entry in timeseries.find_all("point"):
            quantity = float(entry.find("quantity").contents[0])
            if is_import:
                quantity *= -1
            position = int(entry.find("position").contents[0])
            dt = datetime_from_position(datetime_start, position, resolution)
            # Find out whether or not we should update the net production
            exchange_list.append(
                zoneKey=sorted_zone_keys,
                datetime=dt,
                source=SOURCE,
                netFlow=quantity,
                sourceType=EventSourceType.forecasted
                if is_forecast
                else EventSourceType.measured,
            )

    return exchange_list


def parse_prices(
    xml_text: str,
    zoneKey: ZoneKey,
    logger: Logger,
) -> PriceList:
    if not xml_text:
        return PriceList(logger)
    soup = BeautifulSoup(xml_text, "html.parser")
    prices = PriceList(logger)
    for timeseries in soup.find_all("timeseries"):
        currency = str(timeseries.find("currency_unit.name").contents[0])
        resolution = str(timeseries.find("resolution").contents[0])
        datetime_start = datetime.fromisoformat(
            zulu_to_utc(timeseries.find("start").contents[0])
        )
        for entry in timeseries.find_all("point"):
            position = int(entry.find("position").contents[0])
            dt = datetime_from_position(datetime_start, position, resolution)
            prices.append(
                zoneKey=zoneKey,
                datetime=dt,
                price=float(entry.find("price.amount").contents[0]),
                source="entsoe.eu",
                currency=currency,
            )

    return prices


def validate_production(
    datapoint: dict[str, Any], logger: Logger
) -> dict[str, Any] | bool | None:
    """
    Production data can sometimes be available but clearly wrong.

    The most common occurrence is when the production total is very low and main generation types are missing.
    In reality a country's electrical grid could not function in this scenario.

    This function checks datapoints for a selection of countries and returns False if invalid and True otherwise.
    """

    zone_key: str = datapoint["zoneKey"]

    validation_criteria = VALIDATIONS.get(zone_key, {})

    if validation_criteria:
        return validate(datapoint, logger=logger, **validation_criteria)
    return True


@refetch_frequency(timedelta(hours=DEFAULT_LOOKBACK_HOURS_REALTIME))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for all production types in the specified zone.
    Removes any values that are in the future or don't have a datetime associated with them.
    """
    if not session:
        session = Session()
    non_aggregated_data: list[ProductionBreakdownList] = []
    for _zone_key in ZONE_KEY_AGGREGATES.get(zone_key, [zone_key]):
        domain = ENTSOE_DOMAIN_MAPPINGS[_zone_key]
        try:
            raw_production = query_production(
                domain, session, target_datetime=target_datetime
            )
        except Exception as e:
            raise ParserException(
                parser="ENTSOE.py",
                message=f"Failed to fetch production for {_zone_key}",
                zone_key=zone_key,
            ) from e
        if raw_production is None:
            raise ParserException(
                parser="ENTSOE.py",
                message=f"No production data found for {_zone_key}",
                zone_key=zone_key,
            )
        # Aggregated data are regrouped unde the same zone key.
        non_aggregated_data.append(parse_production(raw_production, logger, zone_key))

    aggregated_zone_data = ProductionBreakdownList.merge_production_breakdowns(
        non_aggregated_data, logger
    ).to_list()
    return [x for x in aggregated_zone_data if validate_production(x, logger)]


@refetch_frequency(timedelta(days=1))
def fetch_production_per_units(
    zone_key: str,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Returns all production units and production values."""

    # If no target_datetime is specified, or the target datetime is less
    # than 5 days ago we set the target_datetime to 5 days ago.
    if target_datetime is None or target_datetime > datetime.now(
        tz=timezone.utc
    ) - timedelta(days=5):
        logger.info(
            "This dataset has a publishing guideline of 5 days from the current MTU, setting the target_datetime to 5 days ago to get the latest data."
        )
        target_datetime = datetime.now(tz=timezone.utc) - timedelta(days=5)

    domain = ENTSOE_EIC_MAPPING[zone_key]
    data = []
    # Iterate over all psr types
    for k in ENTSOE_PARAMETER_DESC:
        try:
            raw_production_per_units = query_production_per_units(
                k, domain, session, target_datetime
            )
            if raw_production_per_units is not None:
                values = parse_production_per_units(raw_production_per_units) or []
                for v in values:
                    if not v:
                        continue
                    v["source"] = "entsoe.eu"
                    if v["unitName"] not in ENTSOE_UNITS_TO_ZONE:
                        logger.warning(
                            f"Unknown unit {v['unitName']} with id {v['unitKey']}"
                        )
                    else:
                        v["zoneKey"] = ENTSOE_UNITS_TO_ZONE[v["unitName"]]
                        if v["zoneKey"] == zone_key:
                            data.append(v)
        except Exception as e:
            raise ParserException(
                parser="ENTSOE.py",
                message=f"Failed to fetch data for {k} in {zone_key}",
                zone_key=zone_key,
            ) from e

    return data


def get_raw_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
    forecast: bool = False,
) -> ExchangeList:
    """
    Gets exchange status between two specified zones.
    Removes any datapoints that are in the future.
    """
    if not session:
        session = Session()
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    # This will be filled with a list of raw exchanges to merge
    raw_exchange_lists: list[ExchangeList] = []

    query_function = query_exchange_forecast if forecast else query_exchange

    # This will be filled with a list of domain pairs to fetch
    exchanges_to_fetch: list[list[str]] = []

    if sorted_zone_keys in EXCHANGE_AGGREGATES:
        for domain_pair in EXCHANGE_AGGREGATES[sorted_zone_keys]:
            exchanges_to_fetch.append(domain_pair)
    elif sorted_zone_keys in ENTSOE_EXCHANGE_DOMAIN_OVERRIDE:
        exchanges_to_fetch.append(ENTSOE_EXCHANGE_DOMAIN_OVERRIDE[sorted_zone_keys])
    else:
        exchanges_to_fetch.append(
            [ENTSOE_DOMAIN_MAPPINGS[zone_key1], ENTSOE_DOMAIN_MAPPINGS[zone_key2]]
        )

    def _fetch_and_parse_exchange(
        domain_pair: list[str],
        is_import: bool,
    ) -> ExchangeList:
        """
        Internal function to fetch and parse exchange data
        only used to avoid code duplication in the parent function.
        """
        domain1, domain2 = domain_pair if is_import else domain_pair[::-1]
        try:
            raw_exchange = query_function(domain1, domain2, session, target_datetime)
        except Exception as e:
            raise ParserException(
                parser="ENTSOE.py",
                message=f"Failed to query {'import' if is_import else 'export'} for {domain1} -> {domain2}",
                zone_key=sorted_zone_keys,
            ) from e
        if raw_exchange is None:
            raise ParserException(
                parser="ENTSOE.py",
                message=f"No exchange data found for {domain1} -> {domain2}",
                zone_key=sorted_zone_keys,
            )
        return parse_exchange(
            raw_exchange,
            is_import=is_import,
            sorted_zone_keys=sorted_zone_keys,
            logger=logger,
            is_forecast=forecast,
        )

    # Grab all exchanges
    for domain_pair in exchanges_to_fetch:
        # First we try to get the import data
        raw_exchange_lists.append(
            _fetch_and_parse_exchange(domain_pair, is_import=True)
        )
        # Then we try to get the export data
        raw_exchange_lists.append(
            _fetch_and_parse_exchange(domain_pair, is_import=False)
        )

    return ExchangeList(logger).merge_exchanges(raw_exchange_lists, logger)


@refetch_frequency(timedelta(hours=DEFAULT_LOOKBACK_HOURS_REALTIME))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets exchange status between two specified zones.
    """
    exchanges = get_raw_exchange(
        zone_key1,
        zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    return exchanges.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange_forecast(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets exchange forecast between two specified zones.
    """
    exchanges = get_raw_exchange(
        zone_key1,
        zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        forecast=True,
    )
    return exchanges.to_list()


@refetch_frequency(timedelta(hours=DEFAULT_LOOKBACK_HOURS_REALTIME))
def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets day-ahead price for specified zone."""
    if not session:
        session = Session()

    domain = ENTSOE_PRICE_DOMAIN_MAPPINGS[zone_key]
    try:
        raw_price_data = query_price(domain, session, target_datetime=target_datetime)
    except Exception as e:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"Failed to fetch price for {zone_key}",
            zone_key=zone_key,
        ) from e
    if raw_price_data is None:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No price data found for {zone_key}",
            zone_key=zone_key,
        )
    return parse_prices(raw_price_data, zone_key, logger).to_list()


# ------------------- #
#  Generation
# ------------------- #


@refetch_frequency(timedelta(days=1))
def fetch_generation_forecast(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets generation forecast for specified zone."""
    if not session:
        session = Session()
    generation_list = TotalProductionList(logger)
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    # Grab generation forecast
    try:
        raw_generation_forecast = query_generation_forecast(
            domain, session, target_datetime=target_datetime
        )
    except Exception as e:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"Failed to query generation forecast for {zone_key}",
            zone_key=zone_key,
        ) from e
    if raw_generation_forecast is None:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No generation forecast data returned for {zone_key}",
            zone_key=zone_key,
        )
    parsed = parse_scalar(
        raw_generation_forecast,
        only_inBiddingZone_Domain=True,
    )
    if parsed is None:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No generation forecast data found for {zone_key}",
            zone_key=zone_key,
        )
    for value, dt in parsed:
        generation_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=SOURCE,
            value=value,
            sourceType=EventSourceType.forecasted,
        )

    return generation_list.to_list()


# ------------------- #
#  Consumption
# ------------------- #


def get_raw_consumption_list(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
    forecasted: bool = False,
):
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    query_function = query_consumption_forecast if forecasted else query_consumption
    consumption_list = TotalConsumptionList(logger)
    try:
        raw_data = query_function(domain, session, target_datetime=target_datetime)
    except Exception as e:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"Failed to query {'consumption forecast' if forecasted else 'consumption'} for {zone_key}",
            zone_key=zone_key,
        ) from e
    if raw_data is None:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No {'consumption forcast' if forecasted else 'consumption'} data returned for {zone_key}",
            zone_key=zone_key,
        )
    parsed = parse_scalar(raw_data, only_outBiddingZone_Domain=True)
    if parsed is None:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No {'consumption forecast' if forecasted else 'consumption'} data found for {zone_key}",
            zone_key=zone_key,
        )
    for value, dt in parsed:
        consumption_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=SOURCE,
            consumption=value,
            sourceType=EventSourceType.forecasted
            if forecasted
            else EventSourceType.measured,
        )
    return consumption_list


@refetch_frequency(timedelta(hours=DEFAULT_LOOKBACK_HOURS_REALTIME))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """Gets consumption for a specified zone."""
    session = session or Session()
    return get_raw_consumption_list(
        zone_key, session, target_datetime=target_datetime, logger=logger
    ).to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption_forecast(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets consumption forecast for specified zone."""
    session = session or Session()
    return get_raw_consumption_list(
        zone_key,
        session,
        target_datetime=target_datetime,
        logger=logger,
        forecasted=True,
    ).to_list()


@refetch_frequency(timedelta(days=1))
def fetch_wind_solar_forecasts(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for all production types in the specified zone.
    """
    if not session:
        session = Session()
    raw_forecasts = {}
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    for data_type in ORDERED_FORECAST_TYPES:
        try:
            raw_forecasts[data_type.name] = query_wind_solar_production_forecast(
                domain, session, data_type, target_datetime=target_datetime
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch {data_type.name} wind and solar forecast for {zone_key}: {e}",
                extra={"zone_key": zone_key},
            )
    if raw_forecasts == {}:
        logger.warning(
            f"No wind and solar forecast data found for {zone_key}",
            extra={"zone_key": zone_key},
        )
        return []

    forcast_breakdown_list = ProductionBreakdownList(logger)
    for raw_forecast in raw_forecasts.values():
        parsed_forecast = parse_production(
            raw_forecast, logger, zone_key, forecasted=True
        )
        forcast_breakdown_list = ProductionBreakdownList.update_production_breakdowns(
            forcast_breakdown_list, parsed_forecast, logger
        )

    return forcast_breakdown_list.to_list()


if __name__ == "__main__":
    fetch_price(ZoneKey("FR"))
