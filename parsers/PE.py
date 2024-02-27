#!/usr/bin/env python3
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency

logger = getLogger(__name__)

API_ENDPOINT = "https://www.coes.org.pe/Portal/portalinformacion/generacion"

TIMEZONE = ZoneInfo("America/Lima")

MAP_GENERATION = {
    "DIESEL": "oil",
    "RESIDUAL": "biomass",
    "CARBÓN": "coal",
    "GAS": "gas",
    "HÍDRICO": "hydro",
    "BIOGÁS": "biomass",
    "BAGAZO": "biomass",
    "SOLAR": "solar",
    "EÓLICA": "wind",
}
SOURCE = "coes.org.pe"


def parse_datetime(dt: str):
    return datetime.strptime(dt, "%Y/%m/%d %H:%M:%S").replace(
        tzinfo=TIMEZONE
    ) - timedelta(minutes=30)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("PE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    r = session or Session()

    # To guarantee a full 24 hours of data we must make 2 requests.
    response_url: Response = r.post(
        API_ENDPOINT,
        data={
            "fechaInicial": (target_datetime - timedelta(days=1)).strftime("%d/%m/%Y"),
            "fechaFinal": target_datetime.strftime("%d/%m/%Y"),
            "indicador": 0,
        },
    )
    production_data = response_url.json()["GraficoTipoCombustible"]["Series"]

    all_production_breakdowns: list[ProductionBreakdownList] = []
    for item in production_data:
        production_mode_list = ProductionBreakdownList(logger)
        production_mode = MAP_GENERATION[item["Name"]]
        for data in item["Data"]:
            productionMix = ProductionMix()
            productionMix.add_value(production_mode, round(float(data["Valor"]), 3))
            production_mode_list.append(
                zoneKey=zone_key,
                datetime=parse_datetime(data["Nombre"]),
                source=SOURCE,
                production=productionMix,
            )
        all_production_breakdowns.append(production_mode_list)
    production_events = ProductionBreakdownList.merge_production_breakdowns(
        all_production_breakdowns, logger
    )
    production_events = production_events.to_list()

    # Drop last datapoints if it "looks" incomplete.
    # The last hour often only contains data from some power plants
    # which results in the last datapoint being significantly lower than expected.
    # This is a hacky check, but since we are only potentially discarding the last hour
    # it will be included when the next datapoint comes in anyway.
    # We only run this check when target_datetime is None, as to not affect refetches
    # TODO: remove this in the future, when this is automatically detected by QA layer

    total_production_per_datapoint = [
        sum(d["production"].values()) for d in production_events
    ]
    mean_production = sum(total_production_per_datapoint) / len(
        total_production_per_datapoint
    )
    if (
        total_production_per_datapoint[-1] < mean_production * 0.9
        and target_datetime is None
    ):
        logger.warning(
            "Dropping last datapoint as it is probably incomplete. Total production is less than 90% of the mean."
        )
        production_events = production_events[:-1]
    return production_events
