from datetime import datetime, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionBreakdown, ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException

PARSER = "BG.py"

SOURCE = "eso.bg"
SOURCE_API_URL = "http://www.eso.bg/api/rabota_na_EEC_json.php"

PRODUCTION_TYPES_BG_TO_EN = {
    "АЕЦ": "nuclear",
    "Кондензационни ТЕЦ": "coal",
    "Топлофикационни ТЕЦ": "gas",
    "Заводски ТЕЦ": "gas",
    "ВЕЦ": "hydro",
    "Малки ВЕЦ": "hydro",
    "ВяЕЦ": "wind",
    "ФЕЦ": "solar",
    "Био ТЕЦ": "biomass",
    "Био ЕЦ": "biomass",
    "Товар РБ": "consumption",
}


def _fetch_all_production_events(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: datetime | None,
    logger: Logger,
) -> list[ProductionBreakdown]:
    """Fetches all production events from the backend source API."""
    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    time = datetime.now(timezone.utc)
    response = session.get(SOURCE_API_URL)
    if not response.status_code == 200:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    response_payload = response.json()
    logger.debug(f"Raw generation breakdown: {response_payload}")

    production = {}
    for header, value in response_payload:
        for production_type_bg in PRODUCTION_TYPES_BG_TO_EN:
            if header.startswith(production_type_bg):
                production_type_en = PRODUCTION_TYPES_BG_TO_EN[production_type_bg]
                production[production_type_en] = (
                    production.get(production_type_en, 0.0) + value
                )

    event = ProductionBreakdown.create(
        logger=logger,
        zoneKey=zone_key,
        datetime=time,
        source=SOURCE,
        production=ProductionMix(
            biomass=production.get("biomass"),
            coal=production.get("coal"),
            gas=production.get("gas"),
            geothermal=production.get("geothermal"),
            hydro=production.get("hydro"),
            nuclear=production.get("nuclear"),
            oil=production.get("oil"),
            solar=production.get("solar"),
            unknown=production.get("unknown"),
            wind=production.get("wind"),
        ),
        storage=None,
    )
    return [event]


def fetch_production(
    zone_key: ZoneKey = ZoneKey("BG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    all_production_events = _fetch_all_production_events(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    production_list = ProductionBreakdownList(logger)
    for event in all_production_events:
        production_list.append(
            zoneKey=event.zoneKey,
            datetime=event.datetime,
            source=event.source,
            production=event.production,
            storage=event.storage,
            sourceType=event.sourceType,
        )
    return production_list.to_list()
