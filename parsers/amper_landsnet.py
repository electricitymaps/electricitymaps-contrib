from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException

SOURCE = "amper.landsnet.is"
SOURCE_URL = "https://amper.landsnet.is/generation/api/Values"


def fetch_production(
    zone_key: ZoneKey = ZoneKey("IS"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or Session()
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    res = r.get(SOURCE_URL)
    if not res.ok:
        raise ParserException(
            parser="amper_landsnet.py",
            message=f"Failed to fetch {SOURCE}: {res.status_code}, err: {res.text}",
            zone_key=zone_key,
        )

    obj = res.json()
    mix = ProductionMix(
        geothermal=obj["geothermal"],
        hydro=obj["hydro"],
        oil=obj["oil"],
    )
    breakdowns = ProductionBreakdownList(logger=logger)
    breakdowns.append(
        zoneKey=zone_key,
        datetime=datetime.fromisoformat(obj["timestamp"]).replace(
            tzinfo=ZoneInfo("Atlantic/Reykjavik")
        ),
        production=mix,
        source=SOURCE,
    )
    return breakdowns.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
