#!/usr/bin/env python3

"""Parser for the electricity grid of Chile"""

from collections import defaultdict
from datetime import datetime, timedelta
from logging import Logger, getLogger
from operator import itemgetter
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.config import refetch_frequency

# Historical API
API_BASE_URL = "https://sipub.coordinador.cl/api/v1/recursos/generacion_centrales_tecnologia_horario?"

TIMEZONE = ZoneInfo("Chile/Continental")

TYPE_MAPPING = {
    "hidraulica": "hydro",
    "termica": "unknown",
    "eolica": "wind",
    "solar": "solar",
    "geotermica": "geothermal",
}


def production_processor_historical(raw_data):
    """Takes raw json data and groups by datetime while mapping generation to type.
    Returns a list of dictionaries.
    """

    clean_datapoints = []
    for datapoint in raw_data:
        clean_datapoint = {}
        date, hour = datapoint["fecha"], datapoint["hora"]
        hour -= 1  # `hora` starts at 1
        parsed_datetime = datetime.fromisoformat(date).replace(
            tzinfo=TIMEZONE
        ) + timedelta(hours=hour)
        clean_datapoint["datetime"] = parsed_datetime

        gen_type_es = datapoint["tipo_central"]
        mapped_gen_type = TYPE_MAPPING[gen_type_es]
        value_mw = float(datapoint["generacion_sum"])

        clean_datapoint[mapped_gen_type] = value_mw

        clean_datapoints.append(clean_datapoint)

    combined = defaultdict(dict)
    for elem in clean_datapoints:
        combined[elem["datetime"]].update(elem)

    ordered_data = sorted(combined.values(), key=itemgetter("datetime"))

    return ordered_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("CL-SEN"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime:
        target_datetime_aware = target_datetime.replace(tzinfo=TIMEZONE)
    else:
        target_datetime_aware = datetime.now(tz=TIMEZONE)
    start = (target_datetime_aware + timedelta(days=-1)).date().isoformat()
    end = target_datetime_aware.date().isoformat()

    date_component = f"fecha__gte={start}&fecha__lte={end}"

    # required for access
    headers = {
        "Referer": "https://www.coordinador.cl/operacion/graficos/operacion-real/generacion-real-del-sistema/",
        "Origin": "https://www.coordinador.cl",
    }

    s = session or Session()
    url = API_BASE_URL + date_component

    req = s.get(url, headers=headers)
    raw_data = req.json()["aggs"]
    historical_data = production_processor_historical(raw_data)

    """The last 9 datapoints should be omitted because they usually are incomplete and shouldn't appear on the map."""
    del historical_data[-9:]

    production_list = ProductionBreakdownList(logger)

    for event in historical_data:
        dt = event.pop("datetime")

        production_mix = ProductionMix()
        for key, value in event.items():
            production_mix.add_value(key, value)

        production_list.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production_mix,
            storage=None,
            source="coordinador.cl",
        )

    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
    # For fetching historical data instead, try:
    print(fetch_production(target_datetime=datetime.strptime("20200220", "%Y%m%d")))
