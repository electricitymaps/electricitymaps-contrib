#!/usr/bin/env python3

"""Parser for the electricity grid of Chile"""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session
from urllib3.util.retry import Retry

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.session import mount_retry
from electricitymap.contrib.parsers.lib.utils import get_token

# Hourly generation per plant from the SIP (Sistema de Información Pública) API, see
# https://portal.api.coordinador.cl/documentacion?service=sipubv2. Hours come in a few hours
# late, large plants first, and are filled in during the next day. Small (PMGD) plants keep
# coming in for ~6 days after that, but they are <1% of the energy. History back to at least 2018. Hours are in local time and every day has 24 of them,
# even when the clocks change. Days are queried one at a time: a range only covers its last
# day's first hour.
API_URL = "https://sipub.api.coordinador.cl/generacion-real/v3/findByDate"
PAGE_SIZE = 10_000  # ~33k rows per day, 50k pages time out
# A day is complete when it has its 24 hours, and its emptiest hour has at least this share of
# the plants of its busiest hour: 98-100% for complete days, 40% for a day being published.
MIN_PLANTS_VS_BUSIEST_HOUR = 0.95
# The API answers 429 under load, which clears within ~15 s.
RETRY = Retry(
    total=6,
    backoff_factor=5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)

TIMEZONE = ZoneInfo("Chile/Continental")

# (tipo_tecnologia, subtipo_tecnologia) -> mode
TYPE_MAPPING = {
    ("Solar", None): "solar",
    ("Eólica", None): "wind",
    ("Geotérmica", None): "geothermal",
    ("Hidráulica", "Pasada"): "hydro",
    ("Hidráulica", "Embalse"): "hydro",
    ("Térmica", "Carbón"): "coal",
    ("Térmica", "PetCoke"): "coal",
    ("Térmica", "Gas Natural"): "gas",
    ("Térmica", "Cogeneración"): "gas",
    ("Térmica", "Diésel"): "oil",
    ("Térmica", "Fuel Oil"): "oil",
    ("Térmica", "GLP"): "oil",
    ("Térmica", "Biomasa"): "biomass",
    ("Térmica", "BioGas"): "biomass",
    ("Térmica", "Termosolar"): "solar",
}
# Battery rows are either charging ("Retiro") or discharging ("Inyección"), both positive.
BATTERY_SIGN = {"Retiro": 1, "Inyección": -1}

SOURCE = "coordinador.cl"


def _query(
    session: Session, day: date, user_key: str, page: int, page_size: int
) -> dict[str, Any]:
    response = session.get(
        API_URL,
        params={
            "startDate": day.isoformat(),
            "endDate": day.isoformat(),
            "pageSize": page_size,
            "page": page,
            "user_key": user_key,
        },
    )
    response.raise_for_status()
    return response.json()


def _fetch_day(session: Session, day: date, user_key: str) -> list[dict[str, Any]]:
    """Returns the rows (one per plant and hour) of `day`."""
    rows, page, pages = [], 1, 1
    while page <= pages:
        body = _query(session, day, user_key, page, PAGE_SIZE)
        pages = body["totalPages"]
        rows += body["data"]
        page += 1
    return rows


def _is_complete(rows: list[dict[str, Any]]) -> bool:
    plants_per_hour = Counter(row["fecha_hora"] for row in rows)
    return len(plants_per_hour) == 24 and min(
        plants_per_hour.values()
    ) >= MIN_PLANTS_VS_BUSIEST_HOUR * max(plants_per_hour.values())


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("CL-SEN"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    session = mount_retry(session or Session(), RETRY)
    # Today is never complete. Yesterday is completed during the day, so live runs fall back
    # to the day before until it is.
    yesterday = datetime.now(tz=TIMEZONE).date() - timedelta(days=1)
    days = (
        [min(target_datetime.astimezone(TIMEZONE).date(), yesterday)]
        if target_datetime
        else [yesterday, yesterday - timedelta(days=1)]
    )
    user_key = get_token("CL_SEN_SIP_API_KEY")

    for day in days:
        rows = _fetch_day(session, day, user_key)
        if _is_complete(rows):
            break
        logger.info(f"CL-SEN data for {day} is not completely published yet")
    else:
        raise ParserException(
            "CL.py", f"No completely published day among {days}", zone_key
        )

    production: defaultdict[str, defaultdict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    battery: defaultdict[str, float] = defaultdict(float)
    unknown_types = set()
    for row in rows:
        hour, value = row["fecha_hora"], row["gen_real_mw"] or 0
        kind = (row["tipo_tecnologia"], row["subtipo_tecnologia"])
        if kind[0] == "BESS" and kind[1] in BATTERY_SIGN:
            battery[hour] += BATTERY_SIGN[kind[1]] * value
        else:
            if kind not in TYPE_MAPPING:
                unknown_types.add(kind)
            production[hour][TYPE_MAPPING.get(kind, "unknown")] += value

    for kind in unknown_types:
        logger.warning(f"Unknown CL-SEN technology {kind}, mapped to unknown")

    production_list = ProductionBreakdownList(logger)
    for hour, modes in sorted(production.items()):
        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(hour).replace(tzinfo=TIMEZONE),
            production=ProductionMix(**modes),
            storage=StorageMix(battery=battery.get(hour)),
            source=SOURCE,
        )
    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
