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
    """Get the one-hourly AMM API data for the desired UTC day."""

    now_utc = datetime.now(timezone.utc)
    hour_now_utc = now_utc.replace(minute=0, second=0, microsecond=0)

    target_datetime_utc = target_datetime.astimezone(timezone.utc)

    # The API expects local (TZ) timestamps and can only return one day of data
    # so might need to do multiple api calls if UTC day straddles multiple local days
    target_day_utc = datetime.combine(target_datetime_utc, time(), tzinfo=timezone.utc)

    target_day_utc_start = target_day_utc
    target_day_utc_end = target_day_utc + timedelta(days=1) - timedelta(microseconds=1)

    local_day_of_target_day_utc_start = datetime.combine(
        target_day_utc_start.astimezone(TIMEZONE), time(), tzinfo=TIMEZONE
    )
    local_day_of_target_day_utc_end = datetime.combine(
        target_day_utc_end.astimezone(TIMEZONE), time(), tzinfo=TIMEZONE
    )

    daily_payloads: dict[datetime, list[dict]] = {}
    for local_day in {
        local_day_of_target_day_utc_start,
        local_day_of_target_day_utc_end,
    }:
        response = session.get(URL, params={"dt": local_day.strftime("%d/%m/%Y")})
        if not response.ok:
            raise ParserException(
                PARSER,
                f"Exception when fetching {target.value} error code: {response.status_code}: {response.text}",
            )

        # The JSON data returned by the API is a list of objects, each representing one technology type.
        daily_payloads[local_day] = response.json()

    if not any(daily_payload for daily_payload in daily_payloads.values()):
        raise ParserException(
            PARSER,
            f"Exception when fetching {target.value}: no data available for UTC day {target_day_utc.strftime('%Y-%m-%d %Z')}. "
            f"Note that historical data is only available for the last 1 year.",
        )

    # aggregate all individual hourly items into a dict keyed by common UTC timestamp
    results: dict[datetime, dict] = collections.defaultdict(dict)
    for local_day, daily_payload in daily_payloads.items():
        for row in daily_payload:
            # The API returns hours in the range [1, 24], so each one refers to the
            # past hour (e.g., 1 is the time period [00:00, 01:00)). Shift the hour
            # so each index represents the hour ahead and is in the range [0, 24),
            # e.g., hour 0 represents the period [00:00, 01:00).
            dt_local = local_day + timedelta(hours=int(row["hora"]) - 1)
            dt_utc = dt_local.astimezone(timezone.utc)

            # ignore data outside of range of interest
            if dt_utc < target_day_utc_start or dt_utc > target_day_utc_end:
                continue

            # For live data, the current hour's data isn't finished updating until the hour has passed,
            # so the current hour should not be included in the results.
            if dt_utc >= hour_now_utc:
                continue

            results[dt_utc][row["tipo"]] = row["potencia"]

    return results


def fetch_consumption(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetch a list of hourly consumption data, in MW, for the UTC day of the requested date-time."""

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
    """Fetch a list of hourly production data, in MW, for the UTC day of the requested date-time."""

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
            "unknown",
            # 'BIOMASA/CARBÓN not always present, e.g. 15/07/2023 TZ
            row.get("BIOMASA/CARBÓN", 0.0) + row["CARBÓN/PETCOKE"] + row["SYNGAN"],
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

    target_datetime = datetime.fromisoformat("2023-07-16T12:00:00+00:00")

    print("fetch_production():")
    print(fetch_production())
    print(f"fetch_production(target_datetime={target_datetime.isoformat()!r}):")
    print(fetch_production(target_datetime=target_datetime))

    print("fetch_consumption():")
    print(fetch_consumption())
    print(f"fetch_consumption(target_datetime={target_datetime.isoformat()!r}):")
    print(fetch_consumption(target_datetime=target_datetime))
