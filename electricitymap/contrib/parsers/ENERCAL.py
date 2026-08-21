import json
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.types import ZoneKey

from .lib.exceptions import ParserException

TZ = ZoneInfo("Pacific/Noumea")

SOURCE = "enercal.nc"

INDEX_TO_TYPE_MAP = {0: "solar", 1: "hydro", 2: "wind", 3: "coal", 4: "oil"}


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()

    if target_datetime and target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=TZ)

    if target_datetime is None:
        target_datetime = datetime.now(tz=TZ)

    # No data since 2024-06-30, but the API is still working
    data = session.get(
        "https://www.enercal.nc/wp-content/themes/enercal/ajax-e-co2.php",
        params={"date_day": target_datetime.strftime("%Y-%m-%d")},
    ).json()

    production = ProductionBreakdownList(logger)

    # Reformat data to native values
    mix = [json.loads(m) for m in data["mix"]]
    time = json.loads(data["time"][0])
    prettyTime = json.loads(data["prettyTime"][0])

    if not time:
        raise ParserException(
            "ENERCAL.py",
            f"This parser cannot retrieve data for: {target_datetime}",
            ZoneKey("NC"),
        )

    # Reformat the data to add key value pairs instead of using index values.
    production_data = []
    for i in range(len(time)):
        production_entry = {}
        for index, type_name in INDEX_TO_TYPE_MAP.items():
            production_entry[type_name] = mix[index][i]
        production_data.append(production_entry)

    # Use zip to ensure the same length of the data and make it easier to loop over
    zipped_data = zip(production_data, time, prettyTime, strict=True)

    for production_entry, time, prettyTime in zipped_data:
        production_mix = ProductionMix()
        for production_mode, production_value in production_entry.items():
            production_mix.add_value(production_mode, production_value)
        date_time = datetime.strptime(f"{time}:{prettyTime}", "%Y-%m-%d:%H").replace(
            tzinfo=TZ
        )
        production.append(
            zoneKey=ZoneKey("NC"),
            datetime=date_time,
            production=production_mix,
            source=SOURCE,
        )

    return production.to_list()
