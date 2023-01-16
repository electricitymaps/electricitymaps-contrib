#!/usr/bin/env python3


from datetime import datetime
from logging import Logger, getLogger
from typing import Dict, List, Optional

import arrow
from requests import Session

from .lib.exceptions import ParserException

# Useful links.
# https://en.wikipedia.org/wiki/Electricity_sector_in_Argentina
# https://en.wikipedia.org/wiki/List_of_power_stations_in_Argentina
# http://globalenergyobservatory.org/countryid/10#
# http://www.industcards.com/st-other-argentina.htm

# API Documentation: https://api.cammesa.com/demanda-svc/swagger-ui.html
CAMMESA_DEMANDA_ENDPOINT = (
    "https://api.cammesa.com/demanda-svc/generacion/ObtieneGeneracioEnergiaPorRegion/"
)
CAMMESA_EXCHANGE_ENDPOINT = (
    "https://api.cammesa.com/demanda-svc/demanda/IntercambioCorredoresGeo/"
)
CAMMESA_RENEWABLES_ENDPOINT = "https://cdsrenovables.cammesa.com/exhisto/RenovablesService/GetChartTotalTRDataSource/"

SUPPORTED_EXCHANGES = {
    "AR->CL-SEN": "ARG-CHI",
    "AR->PY": "ARG-PAR",
    "AR->UY": "ARG-URU",
    "AR-NEA->BR-S": "ARG-BRA",
    "AR-BAS->AR-COM": "PBA-COM",
    "AR-CEN->AR-COM": "CEN-COM",
    "AR-CEN->AR-NOA": "CEN-NOA",
    "AR-CUY->AR-COM": "CUY-COM",
    "AR-CEN->AR-CUY": "CEN-CUY",
    "AR-LIT->AR-NEA": "LIT-NEA",
    "AR-BAS->AR-LIT": "PBA-LIT",
    "AR-CUY->AR-NOA": "CUY-NOA",
    "AR-LIT->AR-CEN": "LIT-CEN",
    "AR-LIT->AR-NOA": "LIT-NOA",
    "AR-BAS->AR-CEN": "PBA-CEN",
    "AR-COM->AR-PAT": "COM-PAT",
    "AR-NEA->AR-NOA": "NEA-NOA",
}

EXCHANGE_DIRECTIONS = {  # directions are from second region -> first region
    "AR->CL-SEN": 0,
    "AR->PY": 225,
    "AR->UY": 180,
    "AR-NEA->BR-S": 225,
    "AR-BAS->AR-COM": 45,
    "AR-CEN->AR-COM": 90,
    "AR-CEN->AR-NOA": 315,
    "AR-CUY->AR-COM": 135,
    "AR-CEN->AR-CUY": 45,
    "AR-LIT->AR-NEA": 225,
    "AR-BAS->AR-LIT": 270,
    "AR-CUY->AR-NOA": 45,
    "AR-LIT->AR-CEN": 45,
    "AR-LIT->AR-NOA": 135,
    "AR-BAS->AR-CEN": 135,
    "AR-COM->AR-PAT": 90,
    "AR-NEA->AR-NOA": 180,
}


def fetch_production(
    zone_key="AR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    """Requests up to date list of production mixes (in MW) of a given country."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    current_session = session or Session()

    non_renewables_production: Dict[str, dict] = non_renewables_production_mix(
        zone_key, current_session
    )
    renewables_production: Dict[str, dict] = renewables_production_mix(
        zone_key, current_session
    )

    full_production_list = [
        {
            "datetime": arrow.get(datetime_tz_ar).to("UTC").datetime,
            "zoneKey": zone_key,
            "production": merged_production_mix(
                non_renewables_production[datetime_tz_ar],
                renewables_production[datetime_tz_ar],
            ),
            "capacity": {},
            "storage": {},
            "source": "cammesaweb.cammesa.com",
        }
        for datetime_tz_ar in non_renewables_production
        if datetime_tz_ar in renewables_production
    ]

    return full_production_list


def merged_production_mix(non_renewables_mix: dict, renewables_mix: dict) -> dict:
    """Merges production mix data from different sources. Hydro comes from two
    different sources that are added up."""

    production_mix = {
        "biomass": renewables_mix["biomass"],
        "solar": renewables_mix["solar"],
        "wind": renewables_mix["wind"],
        "hydro": non_renewables_mix["hydro"] + renewables_mix["hydro"],
        "nuclear": non_renewables_mix["nuclear"],
        "unknown": non_renewables_mix["unknown"],
    }

    return production_mix


def renewables_production_mix(zone_key: str, session: Session) -> Dict[str, dict]:
    """Retrieves production mix for renewables using CAMMESA's API"""

    today = arrow.now(tz="America/Argentina/Buenos Aires").format("DD-MM-YYYY")
    params = {"desde": today, "hasta": today}
    renewables_response = session.get(CAMMESA_RENEWABLES_ENDPOINT, params=params)
    assert renewables_response.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={} with payload={}".format(
            zone_key, CAMMESA_RENEWABLES_ENDPOINT, params
        )
    )

    production_list = renewables_response.json()
    sorted_production_list = sorted(production_list, key=lambda d: d["momento"])

    renewables_production: Dict[str, dict] = {
        production_info["momento"]: {
            "biomass": production_info["biocombustible"],
            "hydro": production_info["hidraulica"],
            "solar": production_info["fotovoltaica"],
            "wind": production_info["eolica"],
        }
        for production_info in sorted_production_list
    }

    return renewables_production


def non_renewables_production_mix(zone_key: str, session: Session) -> Dict[str, dict]:
    """Retrieves production mix for non renewables using CAMMESA's API"""

    params = {"id_region": 1002}
    api_cammesa_response = session.get(CAMMESA_DEMANDA_ENDPOINT, params=params)
    assert api_cammesa_response.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={} with payload={}".format(
            zone_key, CAMMESA_DEMANDA_ENDPOINT, params
        )
    )

    production_list = api_cammesa_response.json()
    sorted_production_list = sorted(production_list, key=lambda d: d["fecha"])

    non_renewables_production: Dict[str, dict] = {
        production_info["fecha"]: {
            "hydro": production_info["hidraulico"],
            "nuclear": production_info["nuclear"],
            # As of 2022 thermal energy is mostly natural gas but
            # the data is not split. We put it into unknown for now.
            # More info: see page 21 in https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/Sintesis%20Mensual/Informe%20Mensual_2021-12.pdf
            "unknown": production_info["termico"],
        }
        for production_info in sorted_production_list
    }

    return non_renewables_production


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = sorted([zone_key1, zone_key2])
    sorted_codes = "->".join(sorted_zone_keys)
    flow: Optional[float] = None
    returned_datetime: datetime

    if sorted_codes in SUPPORTED_EXCHANGES:
        current_session = session or Session()

        api_cammesa_response = current_session.get(CAMMESA_EXCHANGE_ENDPOINT)
        assert (
            api_cammesa_response.status_code == 200
        ), f"Exception when fetching exchange for {sorted_codes}: error when calling url={CAMMESA_EXCHANGE_ENDPOINT}"

        exchange_name = SUPPORTED_EXCHANGES[sorted_codes]
        exchange_list = api_cammesa_response.json()
        for exchange in exchange_list["features"]:
            properties = exchange["properties"]
            if properties["nombre"] == exchange_name:
                angle_config = EXCHANGE_DIRECTIONS[sorted_codes]
                given_angle = int(properties["url"][6:])
                flow = int(properties["text"])
                if angle_config != given_angle:
                    flow = -flow
                returned_datetime = datetime.fromisoformat(
                    properties["fecha"][:-2] + ":" + properties["fecha"][-2:]
                )
                break
        if flow is None:
            raise ParserException(
                "AR.py",
                f"Failed fetching exchange for {sorted_zone_keys}",
                sorted_codes,
            )
    else:
        raise NotImplementedError("This exchange is not currently implemented")

    exchange = {
        "sortedZoneKeys": sorted_codes,
        "datetime": returned_datetime,
        "netFlow": flow,
        "source": "cammesaweb.cammesa.com",
    }

    return exchange


def fetch_price(
    zone_key: str = "AR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power price of a given country."""

    raise NotImplementedError("Fetching the price is not currently implemented")


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    print("fetch_exchange(AR, PY) ->")
    print(fetch_exchange("AR", "PY"))
    print("fetch_exchange(AR, UY) ->")
    print(fetch_exchange("AR", "UY"))
    print("fetch_exchange(AR, CL-SEN) ->")
    print(fetch_exchange("AR", "CL-SEN"))
