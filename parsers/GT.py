"""Parse Guatemalan electricity data from the Administrador del Mercado Mayorista (AMM) API."""

import collections
import enum
from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER = "GT.py"
DEFAULT_ZONE_KEY = ZoneKey("GT")
TIMEZONE = ZoneInfo("America/Guatemala")

SOURCE = "wl12.amm.org.gt"
URL = f"https://{SOURCE}/GraficaPW/graficaCombustible"


class ApiKind(enum.Enum):
    PRODUCTION = "production"
    CONSUMPTION = "consumption"


def _get_api_data(
    session: Session,
    target_datetime: datetime,
    target: ApiKind,
) -> dict[datetime, dict]:
    """Get the JSON-formatted response from the AMM API for the desired (local) date-time."""

    target_datetime_utc = target_datetime.astimezone(timezone.utc)
    now_utc = datetime.now(timezone.utc)

    # The API expects local (TZ) timestamps
    target_datetime_local = target_datetime_utc.astimezone(TIMEZONE)
    target_day_local = datetime.combine(target_datetime_local, time(), tzinfo=TIMEZONE)
    today_local = now_utc.astimezone(TIMEZONE)
    response = session.get(URL, params={"dt": target_day_local.strftime("%d/%m/%Y")})
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching {target.value} error code: {response.status_code}: {response.text}",
        )
    response_payload = response.json()
    if not response_payload:
        raise ParserException(
            PARSER,
            f"Exception when fetching {target.value}: no data available for target day {target_day_local.strftime('%Y-%m-%d %Z')}. "
            f"Note that historical data is only available for the last 1 year, and live data is only available after ~9:15 AM UTC ",
        )

    # The JSON data returned by the API is a list of objects, each
    # representing one technology type. Collect this information into a list,
    # with the list index representing the hour of day.
    results = [collections.defaultdict(float) for _ in range(24)]
    for row in response_payload:
        # The API returns hours in the range [1, 24], so each one refers to the
        # past hour (e.g., 1 is the time period [00:00, 01:00)). Shift the hour
        # so each index represents the hour ahead and is in the range [0, 24),
        # e.g., hour 0 represents the period [00:00, 01:00).
        results[int(row["hora"]) - 1][row["tipo"]] = row["potencia"]

    # For live consumption data, an hour's data isn't updated until the hour has passed,
    # so the current (and future) hour(s) should not be included in the results.
    # For live production data, the API will return zero-filled future data until the end of the day,
    # so future hours should not be included in the results.
    is_live_day = target_day_local.date() >= today_local.date()
    if is_live_day:
        cutoff_index = (
            target_datetime_local.hour
            if target == ApiKind.CONSUMPTION
            else target_datetime_local.hour + 1
        )
        results = results[:cutoff_index]

    # return as a dict of API results keyed by UTC timestamp
    return {
        (target_day_local + timedelta(hours=h)).astimezone(timezone.utc): v
        for h, v in enumerate(results)
    }


def fetch_consumption(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetch a list of hourly consumption data, in MW, for the (local) day of the requested date-time."""

    session = session or Session()
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )
    api_data = _get_api_data(
        session, target_datetime=target_datetime, target=ApiKind.CONSUMPTION
    )

    consumption_list = TotalConsumptionList(logger=logger)
    for dt, row in api_data.items():
        consumption = row["DEM SNI"]
        if not consumption:
            continue

        consumption_list.append(
            zoneKey=zone_key,
            datetime=dt,
            consumption=consumption,
            source=SOURCE,
        )
    return consumption_list.to_list()


def fetch_production(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetch a list of hourly production data, in MW, for the (local) day of the requested date-time."""

    session = session or Session()
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )
    api_data = _get_api_data(
        session, target_datetime=target_datetime, target=ApiKind.PRODUCTION
    )

    production_breakdown_list = ProductionBreakdownList(logger)
    for dt, row in api_data.items():
        production_mix = ProductionMix()
        production_mix.add_value("biomass", row["BIOGAS"] + row["BIOMASA"])
        production_mix.add_value("coal", row["CARBÓN"])
        production_mix.add_value("gas", row["GAS NATURAL"])
        production_mix.add_value("geothermal", row["VAPOR"])
        production_mix.add_value("hydro", row["AGUA"])
        production_mix.add_value("oil", row["BUNKER"] + row["DIESEL"])
        production_mix.add_value("solar", row["IRRADIACIÓN"])
        production_mix.add_value(
            "unknown", row["BIOMASA/CARBÓN"] + row["CARBÓN/PETCOKE"] + row["SYNGAN"]
        )
        production_mix.add_value("wind", row["VIENTO"])

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=SOURCE,
            production=production_mix,
        )
    return production_breakdown_list.to_list()


if __name__ == "__main__":
    # Never used by the electricityMap back-end, but handy for testing.

    target_datetime = datetime.fromisoformat("2022-01-01T12:00:00+00:00")

    print("fetch_production():")
    print(fetch_production())
    print(f"fetch_production(target_datetime={target_datetime.isoformat()!r}):")
    print(fetch_production(target_datetime=target_datetime))

    print("fetch_consumption():")
    print(fetch_consumption())
    print(f"fetch_consumption(target_datetime={target_datetime.isoformat()!r}):")
    print(fetch_consumption(target_datetime=target_datetime))
