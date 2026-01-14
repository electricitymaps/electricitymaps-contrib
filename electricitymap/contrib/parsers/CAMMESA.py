#!/usr/bin/env python3


from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

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

# Expected arrow direction if flow is first -> second
EXCHANGE_NAME_DIRECTION_MAPPING = {
    "AR->CL-SEN": ("ARG-CHI", 180),
    "AR->PY": ("ARG-PAR", 45),
    "AR->UY": ("ARG-URU", 0),
    "AR-NEA->BR-S": ("ARG-BRA", 45),
    "AR-BAS->AR-COM": ("PBA-COM", 225),
    "AR-CEN->AR-COM": ("CEN-COM", 270),
    "AR-CEN->AR-NOA": ("CEN-NOA", 135),
    "AR-CUY->AR-COM": ("CUY-COM", 315),
    "AR-CEN->AR-CUY": ("CEN-CUY", 225),
    "AR-LIT->AR-NEA": ("LIT-NEA", 45),
    "AR-BAS->AR-LIT": ("PBA-LIT", 90),
    "AR-CUY->AR-NOA": ("CUY-NOA", 45),
    "AR-LIT->AR-CEN": ("LIT-CEN", 225),
    "AR-LIT->AR-NOA": ("LIT-NOA", 135),
    "AR-BAS->AR-CEN": ("PBA-CEN", 135),
    "AR-COM->AR-PAT": ("COM-PAT", 270),
    "AR-NEA->AR-NOA": ("NEA-NOA", 180),
}

SOURCE = "cammesaweb.cammesa.com"

SPLIT_UNKNOWN_PRODUCTION = {  # To be updated with the latest data when available
    2017: {"oil": 0.12, "gas": 0.85, "coal": 0.03},
    2018: {"oil": 0.07, "gas": 0.90, "coal": 0.03},
    2019: {"oil": 0.04, "gas": 0.95, "coal": 0.01},
    2020: {"oil": 0.075, "gas": 0.90, "coal": 0.025},
    2021: {"oil": 0.12, "gas": 0.85, "coal": 0.03},
    2022: {"oil": 0.17, "gas": 0.80, "coal": 0.03},
}  # source: EIA 2022 (https://www.iea.org/data-and-statistics/data-tools/energy-statistics-data-browser?country=ARGENTINA&fuel=Energy%20supply&indicator=ElecGenByFuel)
df_split_unknown_production = pd.DataFrame(SPLIT_UNKNOWN_PRODUCTION).T
df_split_unknown_production = df_split_unknown_production.reindex(
    range(2017, datetime.now().year + 1), method="ffill"
)


def fetch_production(
    zone_key: ZoneKey = ZoneKey("AR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests up to date list of production mixes (in MW) of a given country."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    current_session = session or Session()

    conventional_production = non_renewables_production_mix(
        zone_key, current_session, logger
    )
    renewables_production = renewables_production_mix(zone_key, current_session, logger)
    # Hydro comes from both conventional and renewables production which are merged together
    return ProductionBreakdownList.merge_production_breakdowns(
        [conventional_production, renewables_production],
        logger,
        matching_timestamps_only=True,
    ).to_list()


def renewables_production_mix(
    zone_key: ZoneKey, session: Session, logger: Logger
) -> ProductionBreakdownList:
    """Retrieves production mix for renewables using CAMMESA's API"""

    today = (
        datetime.now()
        .astimezone(tz=ZoneInfo("America/Argentina/Buenos_Aires"))
        .strftime("%d-%m-%Y")
    )
    params = {"desde": today, "hasta": today}
    renewables_response = session.get(CAMMESA_RENEWABLES_ENDPOINT, params=params)
    assert renewables_response.status_code == 200, (
        "Exception when fetching production for "
        f"{zone_key}: error when calling url={CAMMESA_RENEWABLES_ENDPOINT} with payload={params}"
    )

    production_list = renewables_response.json()
    renewables_production = ProductionBreakdownList(logger)
    for production_info in production_list:
        renewables_production.append(
            zoneKey=zone_key,
            datetime=datetime.strptime(
                production_info["momento"], "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            production=ProductionMix(
                biomass=production_info["biocombustible"],
                hydro=production_info["hidraulica"],
                solar=production_info["fotovoltaica"],
                wind=production_info["eolica"],
            ),
            source=SOURCE,
        )

    return renewables_production


def non_renewables_production_mix(
    zone_key: ZoneKey, session: Session, logger: Logger
) -> ProductionBreakdownList:
    """Retrieves production mix for non renewables using CAMMESA's API"""

    params = {"id_region": 1002}
    api_cammesa_response = session.get(CAMMESA_DEMANDA_ENDPOINT, params=params)
    assert api_cammesa_response.status_code == 200, (
        "Exception when fetching production for "
        f"{zone_key}: error when calling url={CAMMESA_DEMANDA_ENDPOINT} with payload={params}"
    )
    production_list = api_cammesa_response.json()
    conventional_production = ProductionBreakdownList(logger)
    for production_info in production_list:
        # Convert fecha string to datetime and extract the year
        production_datetime = datetime.strptime(
            production_info["fecha"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        production_year = production_datetime.year

        # use the split from EIA 2022 to split the termico production into gas and oil
        for mode in ["gas", "oil", "coal"]:
            production_info[mode] = (
                production_info["termico"]
                * df_split_unknown_production.loc[production_year][mode]
            )  # use the split from EIA 2022 to split the termico production into gas and oil
        conventional_production.append(
            zoneKey=zone_key,
            datetime=production_datetime,
            production=ProductionMix(
                hydro=production_info["hidraulico"],
                nuclear=production_info["nuclear"],
                # As of 2022 thermal energy is mostly natural gas but
                # the data is not split. We put it into unknown for now.
                # More info: see page 21 in https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/Sintesis%20Mensual/Informe%20Mensual_2021-12.pdf
                # unknown=production_info["termico"],
                gas=production_info["gas"],
                oil=production_info["oil"],
                coal=production_info["coal"],
            ),
            source=SOURCE,
        )

    return conventional_production


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two zones."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    if sorted_zone_keys not in EXCHANGE_NAME_DIRECTION_MAPPING:
        raise ParserException(
            parser="CAMMESA.py",
            message="This exchange is not currently implemented",
            zone_key=sorted_zone_keys,
        )

    current_session = session or Session()

    api_cammesa_response = current_session.get(CAMMESA_EXCHANGE_ENDPOINT)
    if not api_cammesa_response.ok:
        raise ParserException(
            parser="CAMMESA.py",
            message=f"Exception when fetching exchange for {sorted_zone_keys}: error when calling url={CAMMESA_EXCHANGE_ENDPOINT}",
            zone_key=sorted_zone_keys,
        )
    exchange_name, expected_angle = EXCHANGE_NAME_DIRECTION_MAPPING[sorted_zone_keys]
    exchange_list = api_cammesa_response.json()["features"]
    exchange_data = next(
        (
            exchange["properties"]
            for exchange in exchange_list
            if exchange["properties"]["nombre"] == exchange_name
        ),
        None,
    )
    if exchange_data is None:
        raise ParserException(
            parser="CAMMESA.py",
            message=f"Exception when fetching exchange for {sorted_zone_keys}: exchange not found",
            zone_key=sorted_zone_keys,
        )
    given_angle = int(exchange_data["url"][6:])
    flow = int(exchange_data["text"])

    # inverse flow if arrow doesn't match expected direction
    if expected_angle != given_angle:
        flow = -flow
    exchange_datetime = datetime.fromisoformat(
        exchange_data["fecha"][:-2] + ":" + exchange_data["fecha"][-2:]
    )
    exchanges = ExchangeList(logger)
    exchanges.append(
        zoneKey=sorted_zone_keys,
        datetime=exchange_datetime,
        netFlow=flow,
        source=SOURCE,
    )
    return exchanges.to_list()


def fetch_price(
    zone_key: str = "AR",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power price of a given country."""

    raise NotImplementedError("Fetching the price is not currently implemented")


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(AR, PY) ->")
    print(fetch_exchange(ZoneKey("AR"), ZoneKey("PY")))
    print("fetch_exchange(AR, UY) ->")
    print(fetch_exchange(ZoneKey("AR"), ZoneKey("UY")))
    print("fetch_exchange(AR, CL-SEN) ->")
    print(fetch_exchange(ZoneKey("AR"), ZoneKey("CL-SEN")))
    print("fetch_exchange(AR-CEN, AR-COM) ->")
    print(fetch_exchange(ZoneKey("AR-CEN"), ZoneKey("AR-COM")))
    print("fetch_exchange(AR-BAS, AR-LIT) ->")
    print(fetch_exchange(ZoneKey("AR-BAS"), ZoneKey("AR-LIT")))
    print("fetch_exchange(AR-COM, AR-PAT) ->")
    print(fetch_exchange(ZoneKey("AR-COM"), ZoneKey("AR-PAT")))
