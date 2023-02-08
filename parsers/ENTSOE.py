#!/usr/bin/env python3
# coding=utf-8

"""
Parser that uses the ENTSOE API to return the following data types.

Consumption
Production
Exchanges
Exchange Forecast
Day-ahead Price
Generation Forecast
Consumption Forecast
"""
import itertools
import re
from collections import defaultdict
from datetime import datetime, timedelta
from logging import Logger, getLogger
from random import shuffle
from typing import Any, Dict, List, Optional, Tuple, Union

import arrow
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from requests import Response, Session

from parsers.lib.config import refetch_frequency

from .lib.exceptions import ParserException
from .lib.utils import get_token, sum_production_dicts
from .lib.validation import validate

ENTSOE_ENDPOINT = "https://web-api.tp.entsoe.eu/api"
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
    "storage": {"hydro storage": ["B10"]},
}
# ENTSOE production type codes mapped to their Electricity Maps production type.
ENTSOE_PARAMETER_BY_GROUP = {
    ENTSOE_key: type
    for key in ["production", "storage"]
    for type, groups in ENTSOE_PARAMETER_GROUPS[key].items()
    for ENTSOE_key in groups
}

# Get all the individual storage parameters in one list
ENTSOE_STORAGE_PARAMETERS = list(
    itertools.chain.from_iterable(ENTSOE_PARAMETER_GROUPS["storage"].values())
)
# Define all ENTSOE zone_key <-> domain mapping
# see https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
ENTSOE_DOMAIN_MAPPINGS: Dict[str, str] = {
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
ENTSOE_EIC_MAPPING: Dict[str, str] = {
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
ZONE_KEY_AGGREGATES: Dict[str, List[str]] = {
    "IT-SO": ["IT-CA", "IT-SO"],
}

# Some exchanges require specific domains
ENTSOE_EXCHANGE_DOMAIN_OVERRIDE: Dict[str, List[str]] = {
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
    "FR-COR-AC->IT-SAR": [
        ENTSOE_DOMAIN_MAPPINGS["IT-SACOAC"],
        ENTSOE_DOMAIN_MAPPINGS["IT-SAR"],
    ],
    "FR-COR-DC->IT-SAR": [
        ENTSOE_DOMAIN_MAPPINGS["IT-SACODC"],
        ENTSOE_DOMAIN_MAPPINGS["IT-SAR"],
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
# Some zone_keys are part of bidding zone domains for price data
ENTSOE_PRICE_DOMAIN_OVERRIDE: Dict[str, str] = {
    "AX": ENTSOE_DOMAIN_MAPPINGS["SE-SE3"],
    "DK-BHM": ENTSOE_DOMAIN_MAPPINGS["DK-DK2"],
    "DE": ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
    "IE": ENTSOE_DOMAIN_MAPPINGS["IE(SEM)"],
    "LU": ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
}

ENTSOE_UNITS_TO_ZONE: Dict[str, str] = {
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

VALIDATIONS: Dict[str, Dict[str, Any]] = {
    # This is a list of criteria to ensure validity of data,
    # used in validate_production()
    # Note that "required" means data is present in ENTSOE.
    # It will still work if data is present but 0.
    # "expected_range" and "floor" only count production and storage
    # - not exchanges!
    "AT": {
        "required": ["hydro"],
    },
    "BA": {"required": ["coal", "hydro", "wind"], "expected_range": (500, 6500)},
    "BE": {
        "required": ["gas", "nuclear"],
        "expected_range": (3000, 25000),
    },
    "BG": {
        "required": ["coal", "nuclear", "hydro"],
        "expected_range": (2000, 20000),
    },
    "CH": {
        "required": ["hydro", "nuclear"],
        "expected_range": (2000, 25000),
    },
    "CZ": {
        # usual load is in 7-12 GW range
        "required": ["coal", "nuclear"],
        "expected_range": (3000, 25000),
    },
    "DE": {
        # Germany sometimes has problems with categories of generation missing from ENTSOE.
        # Normally there is constant production of a few GW from hydro and biomass
        # and when those are missing this can indicate that others are missing as well.
        # We have also never seen unknown being 0.
        # Usual load is in 30 to 80 GW range.
        "required": [
            "coal",
            "gas",
            "nuclear",
            "wind",
            "biomass",
            "hydro",
            "unknown",
            "solar",
        ],
        "expected_range": (20000, 100000),
    },
    "EE": {
        "required": ["coal"],
    },
    "ES": {
        "required": ["coal", "nuclear"],
        "expected_range": (10000, 80000),
    },
    "FI": {
        "required": ["coal", "nuclear", "hydro", "biomass"],
        "expected_range": (2000, 20000),
    },
    "GB": {
        # usual load is in 15 to 50 GW range
        "required": ["coal", "gas", "nuclear"],
        "expected_range": (10000, 80000),
    },
    "GR": {
        "required": ["coal", "gas"],
        "expected_range": (2000, 20000),
    },
    "HR": {
        "required": [
            "coal",
            "gas",
            "wind",
            "biomass",
            "oil",
            "solar",
        ],
    },
    "HU": {
        "required": ["coal", "nuclear"],
    },
    "IE": {
        "required": ["coal"],
        "expected_range": (1000, 15000),
    },
    "IT": {
        "required": ["coal"],
        "expected_range": (5000, 50000),
    },
    "PL": {
        # usual load is in 10-20 GW range and coal is always present
        "required": ["coal"],
        "expected_range": (5000, 35000),
    },
    "PT": {
        "required": ["coal", "gas"],
        "expected_range": (1000, 20000),
    },
    "RO": {
        "required": ["coal", "nuclear", "hydro"],
        "expected_range": (2000, 25000),
    },
    "RS": {
        "required": ["coal"],
    },
    "SE": {
        "required": ["hydro", "nuclear", "wind", "unknown"],
    },
    "SE-SE1": {
        "required": ["hydro", "wind", "unknown", "solar"],
    },
    "SE-SE2": {
        "required": ["gas", "hydro", "wind", "unknown", "solar"],
    },
    "SE-SE3": {
        "required": ["gas", "hydro", "nuclear", "wind", "unknown", "solar"],
    },
    "SE-SE4": {
        "required": ["gas", "hydro", "wind", "unknown", "solar"],
    },
    "SI": {
        # own total generation capacity is around 4 GW
        "required": ["nuclear"],
        "expected_range": (140, 5000),
    },
    "SK": {"required": ["nuclear"]},
}


def closest_in_time_key(
    x, target_datetime: Optional[datetime], datetime_key="datetime"
):
    if target_datetime is None:
        target_datetime = datetime.utcnow()
    if isinstance(target_datetime, datetime):
        return np.abs((x[datetime_key] - target_datetime).seconds)


def query_ENTSOE(
    session: Session,
    params: Dict[str, str],
    target_datetime: Optional[datetime] = None,
    span: tuple = (-48, 24),
    function_name: str = "",
) -> str:
    """
    Makes a standard query to the ENTSOE API with a modifiable set of parameters.
    Allows an existing session to be passed.
    Raises an exception if no API token is found.
    Returns a request object.
    """
    if target_datetime is None:
        target_datetime = datetime.utcnow()
    if isinstance(target_datetime, datetime):
        # make sure we have an arrow object
        params["periodStart"] = (target_datetime + timedelta(hours=span[0])).strftime(
            "%Y%m%d%H00"  # YYYYMMDDHH00
        )
        params["periodEnd"] = (target_datetime + timedelta(hours=span[1])).strftime(
            "%Y%m%d%H00"  # YYYYMMDDHH00
        )
    else:
        raise ParserException(
            parser="ENTSOE.py",
            message="target_datetime has to be a datetime in query_entsoe",
        )

    # Due to rate limiting, we need to spread our requests across different tokens
    tokens = get_token("ENTSOE_TOKEN").split(",")
    # Shuffle the tokens so that we don't always use the same one first.
    shuffle(tokens)
    last_response_if_all_fail = None
    # Try each token until we get a valid response
    for token in tokens:
        params["securityToken"] = token
        response: Response = session.get(ENTSOE_ENDPOINT, params=params)
        if response.ok:
            return response.text
        else:
            last_response_if_all_fail = response
    # If we get here, all tokens failed to fetch valid data
    # and we will check the last response for a error message.
    exception_message = None
    if last_response_if_all_fail is not None:
        soup = BeautifulSoup(last_response_if_all_fail.text, "html.parser")
        text = soup.find_all("text")
        if len(text):
            error_text = soup.find_all("text")[0].prettify()
            if "No matching data found" in error_text:
                exception_message = "No matching data found"
            else:
                exception_message = (
                    f"{function_name} failed in ENTSOE.py. Reason: {error_text}"
                )
        else:
            exception_message = f"{function_name} failed in ENTSOE.py. Reason: {last_response_if_all_fail.text}"

    raise ParserException(
        parser="ENTSOE.py",
        message=exception_message
        if exception_message
        else "An unknown error occured while querying ENTSOE.",
    )


def query_consumption(
    domain: str, session: Session, target_datetime: Optional[datetime] = None
) -> Union[str, None]:

    params = {
        "documentType": "A65",
        "processType": "A16",
        "outBiddingZone_Domain": domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        function_name=query_consumption.__name__,
    )


def query_production(
    in_domain: str, session: Session, target_datetime: Optional[datetime] = None
) -> Union[str, None]:
    params = {
        "documentType": "A75",
        "processType": "A16",  # Realised
        "in_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=(-48, 0),
        function_name=query_production.__name__,
    )


def query_production_per_units(
    psr_type: str,
    domain: str,
    session: Session,
    target_datetime: Optional[datetime] = None,
) -> Union[str, None]:

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
        target_datetime,
        span=(-24, 0),
        function_name=query_production_per_units.__name__,
    )


def query_exchange(
    in_domain: str,
    out_domain: str,
    session: Session,
    target_datetime: Optional[datetime] = None,
) -> Union[str, None]:

    params = {
        "documentType": "A11",
        "in_Domain": in_domain,
        "out_Domain": out_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        function_name=query_exchange.__name__,
    )


def query_exchange_forecast(
    in_domain: str,
    out_domain: str,
    session: Session,
    target_datetime: Optional[datetime] = None,
) -> Union[str, None]:
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
        function_name=query_exchange_forecast.__name__,
    )


def query_price(
    domain: str, session: Session, target_datetime: Optional[datetime] = None
) -> Union[str, None]:

    params = {
        "documentType": "A44",
        "in_Domain": domain,
        "out_Domain": domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        function_name=query_price.__name__,
    )


def query_generation_forecast(
    in_domain: str, session: Session, target_datetime: Optional[datetime] = None
) -> Union[str, None]:
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
        function_name=query_generation_forecast.__name__,
    )


def query_consumption_forecast(
    in_domain: str, session: Session, target_datetime: Optional[datetime] = None
) -> Union[str, None]:
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
        function_name=query_consumption_forecast.__name__,
    )


def query_wind_solar_production_forecast(
    in_domain: str, session: Session, target_datetime: Optional[datetime] = None
) -> Union[str, None]:
    """Gets consumption forecast for 48 hours ahead and previous 24 hours."""

    params = {
        "documentType": "A69",  # Forecast
        "processType": "A01",
        "in_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        function_name=query_wind_solar_production_forecast.__name__,
    )


def datetime_from_position(
    start: arrow.Arrow, position: int, resolution: str
) -> datetime:
    """Finds time granularity of data."""

    m = re.search(r"PT(\d+)([M])", resolution)
    if m is not None:
        digits = int(m.group(1))
        scale = m.group(2)
        if scale == "M":
            return start.shift(minutes=(position - 1) * digits).datetime
    raise NotImplementedError("Could not recognise resolution %s" % resolution)


def parse_scalar(
    xml_text: str,
    only_inBiddingZone_Domain: bool = False,
    only_outBiddingZone_Domain: bool = False,
) -> Union[Tuple[List[float], List[datetime]], None]:

    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    values = []
    datetimes = []
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start = arrow.get(timeseries.find_all("start")[0].contents[0])
        if only_inBiddingZone_Domain:
            if not len(timeseries.find_all("inBiddingZone_Domain.mRID".lower())):
                continue
        elif only_outBiddingZone_Domain:
            if not len(timeseries.find_all("outBiddingZone_Domain.mRID".lower())):
                continue
        for entry in timeseries.find_all("point"):
            position = int(entry.find_all("position")[0].contents[0])
            value = float(entry.find_all("quantity")[0].contents[0])
            datetime = datetime_from_position(datetime_start, position, resolution)
            values.append(value)
            datetimes.append(datetime)

    return values, datetimes


def parse_production(
    xml_text,
) -> Union[Tuple[List[Dict[str, Any]], List[datetime]], None]:

    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    productions = []
    datetimes = []
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start: arrow.Arrow = arrow.get(
            timeseries.find_all("start")[0].contents[0]
        )
        is_production = (
            len(timeseries.find_all("inBiddingZone_Domain.mRID".lower())) > 0
        )
        psr_type = str(
            timeseries.find_all("mktpsrtype")[0].find_all("psrtype")[0].contents[0]
        )

        for entry in timeseries.find_all("point"):
            quantity = float(entry.find_all("quantity")[0].contents[0])
            position = int(entry.find_all("position")[0].contents[0])
            datetime = datetime_from_position(datetime_start, position, resolution)
            try:
                i = datetimes.index(datetime)
                if is_production:
                    productions[i][psr_type] += quantity
                elif psr_type in ENTSOE_STORAGE_PARAMETERS:
                    # Only include consumption if it's for storage. In other cases
                    # it is power plant self-consumption which should be ignored.
                    productions[i][psr_type] -= quantity
            except ValueError:  # Not in list
                datetimes.append(datetime)
                productions.append(defaultdict(lambda: 0))
                productions[-1][psr_type] = quantity if is_production else -1 * quantity
    return productions, datetimes


def parse_self_consumption(xml_text: str):
    """
    Parses the XML text and returns a dict of datetimes to the total self-consumption
    value from all sources.
    Self-consumption is the electricity used by a generation source.
    This is defined as any consumption source (i.e. outBiddingZone_Domain.mRID)
    that is not storage, e.g. consumption for B04 (Fossil Gas) is counted as
    self-consumption, but consumption for B10 (Hydro Pumped Storage) is not.

    In most cases, total self-consumption is reported by ENTSOE as 0,
    therefore the returned dict only includes datetimes where the value > 0.
    """

    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    res = {}
    for timeseries in soup.find_all("timeseries"):
        is_consumption = (
            len(timeseries.find_all("outBiddingZone_Domain.mRID".lower())) > 0
        )
        if not is_consumption:
            continue
        psr_type = str(
            timeseries.find_all("mktpsrtype")[0].find_all("psrtype")[0].contents[0]
        )
        if psr_type in ENTSOE_STORAGE_PARAMETERS:
            continue
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start: arrow.Arrow = arrow.get(
            timeseries.find_all("start")[0].contents[0]
        )

        for entry in timeseries.find_all("point"):
            quantity = float(entry.find_all("quantity")[0].contents[0])
            if quantity == 0:
                continue
            position = int(entry.find_all("position")[0].contents[0])
            datetime = datetime_from_position(datetime_start, position, resolution)
            res[datetime] = res[datetime] + quantity if datetime in res else quantity

    return res


def parse_production_per_units(xml_text: str) -> Union[Any, None]:
    values = {}

    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start: arrow.Arrow = arrow.get(
            timeseries.find_all("start")[0].contents[0]
        )
        is_production = (
            len(timeseries.find_all("inBiddingZone_Domain.mRID".lower())) > 0
        )
        psr_type = str(
            timeseries.find_all("mktpsrtype")[0].find_all("psrtype")[0].contents[0]
        )
        unit_key = str(
            timeseries.find_all("mktpsrtype")[0]
            .find_all("powersystemresources")[0]
            .find_all("mrid")[0]
            .contents[0]
        )
        unit_name = str(
            timeseries.find_all("mktpsrtype")[0]
            .find_all("powersystemresources")[0]
            .find_all("name")[0]
            .contents[0]
        )
        if not is_production:
            continue
        for entry in timeseries.find_all("point"):
            quantity = float(entry.find_all("quantity")[0].contents[0])
            position = int(entry.find_all("position")[0].contents[0])
            datetime = datetime_from_position(datetime_start, position, resolution)
            key = (unit_key, datetime)
            if key in values:
                if is_production:
                    values[key]["production"] += quantity
                else:
                    values[key]["production"] -= quantity
            else:
                values[key] = {
                    "datetime": datetime,
                    "production": quantity,
                    "productionType": ENTSOE_PARAMETER_BY_GROUP[psr_type],
                    "unitKey": unit_key,
                    "unitName": unit_name,
                }

    return values.values()


def parse_exchange(
    xml_text: str,
    is_import: bool,
    quantities: Optional[List[float]] = None,
    datetimes: Optional[List[datetime]] = None,
) -> Union[Tuple[List[float], List[datetime]], None]:

    if not xml_text:
        return None
    quantities = quantities or []
    datetimes = datetimes or []
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    for timeseries in soup.find_all("timeseries"):
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start: arrow.Arrow = arrow.get(
            timeseries.find_all("start")[0].contents[0]
        )
        # Only use contract_marketagreement.type == A01 (Total to avoid double counting some columns)
        if (
            timeseries.find_all("contract_marketagreement.type")
            and timeseries.find_all("contract_marketagreement.type")[0].contents[0]
            != "A05"
        ):
            continue

        for entry in timeseries.find_all("point"):
            quantity = float(entry.find_all("quantity")[0].contents[0])
            if not is_import:
                quantity *= -1
            position = int(entry.find_all("position")[0].contents[0])
            datetime = datetime_from_position(datetime_start, position, resolution)
            # Find out whether or not we should update the net production
            try:
                i = datetimes.index(datetime)
                quantities[i] += quantity
            except ValueError:  # Not in list
                quantities.append(quantity)
                datetimes.append(datetime)

    return quantities, datetimes


def parse_price(
    xml_text: str,
) -> Union[Tuple[List[float], List[str], List[datetime]], None]:

    if not xml_text:
        return None
    soup = BeautifulSoup(xml_text, "html.parser")
    # Get all points
    prices: List[float] = []
    currencies: List[str] = []
    datetimes: List[datetime] = []
    for timeseries in soup.find_all("timeseries"):
        currency = str(timeseries.find_all("currency_unit.name")[0].contents[0])
        resolution = str(timeseries.find_all("resolution")[0].contents[0])
        datetime_start: arrow.Arrow = arrow.get(
            timeseries.find_all("start")[0].contents[0]
        )
        for entry in timeseries.find_all("point"):
            position = int(entry.find_all("position")[0].contents[0])
            dt = datetime_from_position(datetime_start, position, resolution)
            prices.append(float(entry.find_all("price.amount")[0].contents[0]))
            datetimes.append(dt)
            currencies.append(currency)

    return prices, currencies, datetimes


def validate_production(
    datapoint: Dict[str, Any], logger: Logger
) -> Union[Dict[str, Any], bool, None]:
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

    # NOTE: Why are there sepcial checks for these zones?
    if zone_key.startswith("DK-"):
        return validate(datapoint, logger=logger, required=["coal", "solar", "wind"])

    if zone_key.startswith("NO-"):
        return validate(datapoint, logger=logger, required=["hydro"])

    return True


def get_wind(values):
    if "Wind Onshore" in values or "Wind Offshore" in values:
        return values.get("Wind Onshore", 0) + values.get("Wind Offshore", 0)


@refetch_frequency(timedelta(days=2))
def fetch_consumption(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    """Gets consumption for a specified zone."""
    session = session or Session()
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    # Grab consumption
    parsed = None
    raw_consumption = query_consumption(domain, session, target_datetime)
    if raw_consumption is not None:
        parsed = parse_scalar(
            raw_consumption,
            only_outBiddingZone_Domain=True,
        )
    if parsed is not None:
        quantities, datetimes = parsed
        # Add power plant self-consumption data.
        # This is reported as part of the production data by ENTSOE.
        # self_consumption is a dict of datetimes to the total self-consumption value from all sources.
        # Only datetimes where the value > 0 are included.
        self_consumption = None
        raw_production = query_production(domain, session, target_datetime)
        if raw_production is not None:
            self_consumption = parse_self_consumption(
                raw_production,
            )
        if self_consumption is not None:
            for dt, value in self_consumption.items():
                try:
                    i = datetimes.index(dt)
                except ValueError:
                    logger.warning(
                        f"No corresponding consumption value found for self-consumption at {dt}"
                    )
                    continue
                quantities[i] += value
            # if a target_datetime was requested, we return everything
            if target_datetime:
                return [
                    {
                        "zoneKey": zone_key,
                        "datetime": dt,
                        "consumption": quantity,
                        "source": "entsoe.eu",
                    }
                    for dt, quantity in zip(datetimes, quantities)
                ]
            # else we keep the last stored value
            # Note, this may not include self-consumption data as sometimes consumption
            # data is available for a given TZ a few minutes before production data is.
            dt, quantity = datetimes[-1], quantities[-1]
            if dt not in self_consumption:
                logger.warning(
                    f"Self-consumption data not yet available for {zone_key} at {dt}"
                )
            data = {
                "zoneKey": zone_key,
                "datetime": dt,
                "consumption": quantity,
                "source": "entsoe.eu",
            }
            return data


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for all production types in the specified zone.
    Removes any values that are in the future or don't have a datetime associated with them.
    """
    if not session:
        session = Session()
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    # Grab production
    parsed = parse_production(
        query_production(domain, session, target_datetime=target_datetime)
    )

    if not parsed:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No production data found for {zone_key}",
            zone_key=zone_key,
        )

    productions, production_dates = parsed

    data = []
    for i in range(len(production_dates)):
        production_values = {k: v for k, v in productions[i].items()}
        production_date = production_dates[i]

        production_types = {"production": {}, "storage": {}}
        for key in ["production", "storage"]:
            parameter_groups = ENTSOE_PARAMETER_GROUPS[key]
            multiplier = -1 if key == "storage" else 1

            for fuel, groups in parameter_groups.items():
                has_value = any(
                    [production_values.get(grp) is not None for grp in groups]
                )
                if has_value:
                    value = sum([production_values.get(grp, 0) for grp in groups])
                    value *= multiplier
                else:
                    value = None

                production_types[key][fuel] = value

        data.append(
            {
                "zoneKey": zone_key,
                "datetime": production_date,
                "production": production_types["production"],
                "storage": {
                    "hydro": production_types["storage"]["hydro storage"],
                },
                "source": "entsoe.eu",
            }
        )

        for d in data:
            for k, v in d["production"].items():
                if v is None:
                    continue
                if v < 0 and v > -50:
                    # Set small negative values to 0
                    logger.warning(
                        "Setting small value of %s (%s) to 0." % (k, v),
                        extra={"key": zone_key},
                    )
                    d["production"][k] = 0

    return list(filter(lambda x: validate_production(x, logger), data))


# TODO: generalize and move to lib.utils so other parsers can reuse it. (it's
# currently used by US_SEC.)
def merge_production_outputs(parser_outputs, merge_zone_key, merge_source=None):
    """
    Given multiple parser outputs, sum the production and storage of corresponding datetimes to create a production list.
    This will drop rows where the datetime is missing in at least a parser_output.
    """
    if len(parser_outputs) == 0:
        return []
    if merge_source is None:
        merge_source = parser_outputs[0][0]["source"]
    prod_and_storage_dfs = [
        pd.DataFrame(output).set_index("datetime")[["production", "storage"]]
        for output in parser_outputs
    ]
    to_return = prod_and_storage_dfs[0]
    for prod_and_storage in prod_and_storage_dfs[1:]:
        # `inner` join drops rows where one of the production is missing
        to_return = to_return.join(prod_and_storage, how="inner", rsuffix="_other")
        to_return["production"] = to_return.apply(
            lambda row: sum_production_dicts(row.production, row.production_other),
            axis=1,
        )
        to_return["storage"] = to_return.apply(
            lambda row: sum_production_dicts(row.storage, row.storage_other), axis=1
        )
        to_return = to_return[["production", "storage"]]

    return [
        {
            "datetime": dt.to_pydatetime(),
            "production": row.production,
            "storage": row.storage,
            "source": merge_source,
            "zoneKey": merge_zone_key,
        }
        for dt, row in to_return.iterrows()
    ]


@refetch_frequency(timedelta(days=2))
def fetch_production_aggregate(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if zone_key not in ZONE_KEY_AGGREGATES:
        raise ValueError("Unknown aggregate key %s" % zone_key)

    return merge_production_outputs(
        [
            fetch_production(k, session, target_datetime, logger)
            for k in ZONE_KEY_AGGREGATES[zone_key]
        ],
        zone_key,
    )


@refetch_frequency(timedelta(days=1))
def fetch_production_per_units(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Returns all production units and production values."""
    if not session:
        session = Session()
    domain = ENTSOE_EIC_MAPPING[zone_key]
    data = []
    # Iterate over all psr types
    for k in ENTSOE_PARAMETER_DESC.keys():
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
                    if not v["unitName"] in ENTSOE_UNITS_TO_ZONE:
                        logger.warning(
                            f"Unknown unit {v['unitName']} with id {v['unitKey']}"
                        )
                    else:
                        v["zoneKey"] = ENTSOE_UNITS_TO_ZONE[v["unitName"]]
                        if v["zoneKey"] == zone_key:
                            data.append(v)
        except:
            ParserException(
                parser="ENTSOE.py",
                message=f"Failed to fetch data for {k} in {zone_key}",
                zone_key=zone_key,
            )

    return data


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets exchange status between two specified zones.
    Removes any datapoints that are in the future.
    """
    if not session:
        session = Session()
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    key = "->".join(sorted_zone_keys)
    if key in ENTSOE_EXCHANGE_DOMAIN_OVERRIDE:
        domain1, domain2 = ENTSOE_EXCHANGE_DOMAIN_OVERRIDE[key]
    else:
        domain1 = ENTSOE_DOMAIN_MAPPINGS[zone_key1]
        domain2 = ENTSOE_DOMAIN_MAPPINGS[zone_key2]
    # Create a hashmap with key (datetime)
    exchange_hashmap = {}
    # Grab exchange
    # Import
    raw_exchange = query_exchange(domain1, domain2, session, target_datetime)
    if raw_exchange is not None:
        parsed = parse_exchange(
            raw_exchange,
            is_import=True,
        )
        if parsed:
            # Export
            raw_exchange = query_exchange(domain2, domain1, session, target_datetime)
            if raw_exchange is not None:
                parsed = parse_exchange(
                    xml_text=raw_exchange,
                    is_import=False,
                    quantities=parsed[0],
                    datetimes=parsed[1],
                )
                if parsed:
                    quantities, datetimes = parsed
                    for i in range(len(quantities)):
                        exchange_hashmap[datetimes[i]] = quantities[i]

        # Remove all dates in the future
        exchange_dates = sorted(set(exchange_hashmap.keys()), reverse=True)
        exchange_dates = list(filter(lambda x: x <= arrow.now(), exchange_dates))
        if not len(exchange_dates):
            raise ParserException(parser="ENTSOE.py", message="No exchange data found")
        data = []
        for exchange_date in exchange_dates:
            net_flow = float(exchange_hashmap[exchange_date])
            data.append(
                {
                    "sortedZoneKeys": key,
                    "datetime": exchange_date,
                    "netFlow": net_flow
                    if zone_key1[0] == sorted_zone_keys
                    else -1 * net_flow,
                    "source": "entsoe.eu",
                }
            )

        return data
    else:
        raise ParserException(
            parser="entsoe.eu",
            message=f"No exchange data found for {zone_key1} -> {zone_key2}",
        )


@refetch_frequency(timedelta(days=2))
def fetch_exchange_forecast(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets exchange forecast between two specified zones."""
    if not session:
        session = Session()
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    key = "->".join(sorted_zone_keys)
    if key in ENTSOE_EXCHANGE_DOMAIN_OVERRIDE:
        domain1, domain2 = ENTSOE_EXCHANGE_DOMAIN_OVERRIDE[key]
    else:
        domain1 = ENTSOE_DOMAIN_MAPPINGS[zone_key1]
        domain2 = ENTSOE_DOMAIN_MAPPINGS[zone_key2]
    # Create a hashmap with key (datetime)
    exchange_hashmap = {}
    # Grab exchange
    # Import
    parsed = None
    raw_exchange_forecast = query_exchange_forecast(
        domain1, domain2, session, target_datetime=target_datetime
    )
    if raw_exchange_forecast is not None:
        parsed = parse_exchange(
            raw_exchange_forecast,
            is_import=True,
        )
    if parsed is not None:
        # Export
        raw_exchange_forecast = query_exchange_forecast(
            domain2, domain1, session, target_datetime=target_datetime
        )
        if raw_exchange_forecast is not None:
            parsed = parse_exchange(
                xml_text=raw_exchange_forecast,
                is_import=False,
                quantities=parsed[0],
                datetimes=parsed[1],
            )
        if parsed is not None:
            quantities, datetimes = parsed
            for i in range(len(quantities)):
                exchange_hashmap[datetimes[i]] = quantities[i]

    # Remove all dates in the future
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    exchange_dates = list(sorted(set(exchange_hashmap.keys()), reverse=True))
    if not len(exchange_dates):
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No exchange forecast data found for {zone_key1} -> {zone_key2}",
        )
    data = []
    for exchange_date in exchange_dates:
        netFlow = exchange_hashmap[exchange_date]
        data.append(
            {
                "sortedZoneKeys": key,
                "datetime": exchange_date,
                "netFlow": netFlow
                if zone_key1[0] == sorted_zone_keys
                else -1 * netFlow,
                "source": "entsoe.eu",
            }
        )
    return data


@refetch_frequency(timedelta(days=2))
def fetch_price(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets day-ahead price for specified zone."""
    # Note: This is day-ahead prices
    if not session:
        session = Session()
    if zone_key in ENTSOE_PRICE_DOMAIN_OVERRIDE:
        domain = ENTSOE_PRICE_DOMAIN_OVERRIDE[zone_key]
    else:
        domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    parsed = None
    # Grab consumption
    raw_price = query_price(domain, session, target_datetime=target_datetime)
    if raw_price is not None:
        parsed = parse_price(raw_price)
    if parsed is not None:
        data = []
        prices, currencies, datetimes = parsed
        for i in range(len(prices)):
            data.append(
                {
                    "zoneKey": zone_key,
                    "datetime": datetimes[i],
                    "currency": currencies[i],
                    "price": prices[i],
                    "source": "entsoe.eu",
                }
            )

        return data
    else:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No price data found for {zone_key}",
            zone_key=zone_key,
        )


@refetch_frequency(timedelta(days=2))
def fetch_generation_forecast(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets generation forecast for specified zone."""
    if not session:
        session = Session()
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    parsed = None
    # Grab consumption
    test = query_generation_forecast(domain, session, target_datetime=target_datetime)
    if test is not None:
        parsed = parse_scalar(
            test,
            only_inBiddingZone_Domain=True,
        )
    if parsed is not None:
        data = []
        values, datetimes = parsed
        for i in range(len(values)):
            data.append(
                {
                    "zoneKey": zone_key,
                    "datetime": datetimes[i],
                    "value": values[i],
                    "source": "entsoe.eu",
                }
            )

        return data
    else:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No generation forecast data found for {zone_key}",
            zone_key=zone_key,
        )


@refetch_frequency(timedelta(days=2))
def fetch_consumption_forecast(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets consumption forecast for specified zone."""
    if not session:
        session = Session()
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    # Grab consumption
    parsed = None
    raw_consumption_forecast = query_consumption_forecast(
        domain, session, target_datetime=target_datetime
    )
    if raw_consumption_forecast is not None:
        parsed = parse_scalar(
            raw_consumption_forecast,
            only_outBiddingZone_Domain=True,
        )
    if parsed is not None:
        data = []
        values, datetimes = parsed
        for i in range(len(values)):
            data.append(
                {
                    "zoneKey": zone_key,
                    "datetime": datetimes[i],
                    "value": values[i],
                    "source": "entsoe.eu",
                }
            )

        return data
    else:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No consumption forecast found for {zone_key}",
            zone_key=zone_key,
        )


@refetch_frequency(timedelta(days=2))
def fetch_wind_solar_forecasts(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for all production types in the specified zone.
    Removes any values that are in the future or don't have a datetime associated with them.
    """
    if not session:
        session = Session()
    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]
    # Grab production
    parsed = parse_production(
        query_wind_solar_production_forecast(
            domain, session, target_datetime=target_datetime
        )
    )

    if not parsed:
        raise ParserException(
            parser="ENTSOE.py",
            message=f"No production per mode forecast data found for {zone_key}",
            zone_key=zone_key,
        )

    productions, production_dates = parsed

    data = []
    for i in range(len(production_dates)):
        production_values = {
            ENTSOE_PARAMETER_DESC[k]: v for k, v in productions[i].items()
        }
        production_date = production_dates[i]

        data.append(
            {
                "zoneKey": zone_key,
                "datetime": production_date,
                "production": {
                    "solar": production_values.get("Solar", None),
                    "wind": get_wind(production_values),
                },
                "source": "entsoe.eu",
            }
        )

    return data
