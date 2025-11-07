from datetime import datetime
from logging import Logger, getLogger
from pprint import pprint
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAM = "?host=https://hydroquebec.com"
DATA_PATH = "data/documents-donnees/donnees-ouvertes/json"
PRODUCTION_URL = f"{US_PROXY}/{DATA_PATH}/production.json{HOST_PARAM}"
CONSUMPTION_URL = f"{US_PROXY}/{DATA_PATH}/demande.json{HOST_PARAM}"
SOURCE = "hydroquebec.com"
TIMEZONE = ZoneInfo("America/Montreal")

MODE_MAPPING = {
    "hydraulique": "hydro",
    "thermique": "gas",  # See Github issue #3218, Québec's thermal generation is at Bécancour gas turbine.
    "solaire": "solar",
    "eolien": "wind",
    "autres": "biomass",  # Other renewables, mostly biomass. See Github #3218
}

IGNORED_KEYS = {"total"}


def fetch_production(
    zone_key: ZoneKey = ZoneKey("CA-QC"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given region."""

    if target_datetime is not None:
        raise NotImplementedError(
            "CA-QC parser does not support historical data requests."
        )

    data = _fetch_quebec_production(session)
    production_breakdown_list = ProductionBreakdownList(logger)
    now = datetime.now(tz=TIMEZONE)

    for elem in data:
        values = elem["valeurs"]
        if not isinstance(values, dict):
            continue

        # Remove ignored keys and skip if no meaningful data remains
        for key in IGNORED_KEYS:
            values.pop(key, None)
        if not values:
            continue

        # Parse timestamp and skip if invalid or future
        if not isinstance(elem["date"], str):
            continue
        timestamp = datetime.fromisoformat(elem["date"]).replace(tzinfo=TIMEZONE)
        if timestamp > now:
            continue

        # Process production data
        production = ProductionMix()
        for key, value in values.items():
            if key in MODE_MAPPING:
                production.add_value(
                    MODE_MAPPING[key], value, correct_negative_with_zero=True
                )
            else:
                logger.warning(
                    f"CA-QC: Unknown production mode '{key}' in data from hydroquebec"
                )

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=production,
            source=SOURCE,
        )
    return production_breakdown_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("CA-QC"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    data = _fetch_quebec_consumption(session)

    consumption = TotalConsumptionList(logger)
    for elem in data:
        if "demandeTotal" in elem["valeurs"]:
            consumption.append(
                zoneKey=zone_key,
                datetime=datetime.fromisoformat(elem["date"]).replace(tzinfo=TIMEZONE),
                consumption=elem["valeurs"]["demandeTotal"],
                source=SOURCE,
            )
    return consumption.to_list()


def _fetch_quebec_production(
    session: Session | None = None, logger: Logger = getLogger(__name__)
) -> list[dict[str, str | dict[str, float]]]:
    s = session or Session()
    response = s.get(PRODUCTION_URL)

    if not response.ok:
        logger.info(
            f"CA-QC: failed getting requested production data from hydroquebec - URL {PRODUCTION_URL}"
        )
    return response.json()["details"]


def _fetch_quebec_consumption(
    session: Session | None = None, logger: Logger = getLogger(__name__)
) -> list[dict[str, Any]]:
    s = session or Session()
    response = s.get(CONSUMPTION_URL)

    if not response.ok:
        logger.info(
            f"CA-QC: failed getting requested consumption data from hydroquebec - URL {CONSUMPTION_URL}"
        )
    return response.json()["details"]


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    test_logger = getLogger(__name__)

    print("fetch_production() ->")
    pprint(fetch_production(logger=test_logger))

    print("fetch_consumption() ->")
    pprint(fetch_consumption(logger=test_logger))
