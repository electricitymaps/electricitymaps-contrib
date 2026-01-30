from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

# The request library is used to fetch content through HTTP
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException

NESO_API = "https://api.neso.energy/api/3/action/datastore_search_sql"


def fetch_production(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """
        Requests the last known production mix (in MW) of a given country.

        Arguments:
        ----------
        zone_key: used in case a parser is able to fetch multiple countries
        session: request session passed in order to re-use an existing session
        target_datetime: the datetime for which we want production data. If not
          provided, we should default it to now. If past data is not available,
          raise a ParserException. Beware that the provided target_datetime is
          UTC. To convert to local timezone, you can use
          `target_datetime = target_datetime.astimezone(tz=ZoneInfo('America/New_York'))`.
        logger: an instance of a `logging.Logger` that will be passed by the
          backend. Information logged will be publicly available so that correct
          execution of the logger can be checked. All Exceptions will automatically
          be logged, so when something's wrong, simply raise an Exception (with an
          explicit text). Use `logger.warning` or `logger.info` for information
          that can useful to check if the parser is working correctly. A default
          logger is used so that logger output can be seen when coding / debugging.

        Returns:
        --------
        If no data can be fetched, any falsy value (None, [], False) will be
          ignored by the backend. If there is no data because the source may have
          changed or is not available, raise an ParserException.

        A  ProductionBreakdownList should be returned containing all ProductionBreakdown
        events. Each ProductionBreakdown event should contain a datetime, a zoneKey,
        a ProductionMix, a source and optionally a StorageMix.
        The ProductionMix should contain the production breakdown for each fuel type.

    -     A  ProductionBreakdownList contains all ProductionBreakdown events.
    -     Each ProductionBreakdown event contains a datetime, a zoneKey,
       a ProductionMix, a source and optionally a StorageMix.
    -     The ProductionMix contains the production breakdown for each fuel type.
    -     The StorageMix contains the storage breakdown for each storage type.


    """

    if target_datetime is None:
        target_datetime = datetime.now(tz=ZoneInfo("UTC"))
    elif target_datetime > datetime(year=2009, month=1, day=1):
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        target_datetime = target_datetime.astimezone(ZoneInfo("London"))
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise ParserException(
            "example_parser.py",
            "This parser is not yet able to parse dates before 2009-01-01",
            zone_key,
        )

    start_datetime = target_datetime - timedelta(days=1)

    sql_query = f"""SELECT * FROM  "f93d1835-75bc-43e5-84ad-12472b180a98" WHERE "DATETIME" >= '{start_datetime.strftime("%Y-%m-%d")}' AND "DATETIME" < '{target_datetime.strftime("%Y-%m-%d")}' ORDER BY "DATETIME" ASC"""
    params = {"sql": sql_query}

    res: Response = session.get(NESO_API, params=params)
    if not res.status_code == 200:
        raise ParserException(
            "example_parser.py",
            f"Exception when fetching production error code: {res.status_code}: {res.text}",
            zone_key,
        )

    obj = res.json()

    production_list = ProductionBreakdownList(logger=logger)

    for item in obj["productionMix"]:
        # You can create the production mix directly
        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(item["datetime"]),
            production=ProductionMix(
                biomass=item["biomass"],
                coal=item["coal"],
                gas=item["gas"],
                hydro=item["hydro"],
                nuclear=item["nuclear"],
                oil=item["oil"],
                solar=item["solar"],
                wind=item["wind"],
                geothermal=item["geothermal"],
                unknown=(
                    item["unknown"]
                    if item["unknown"] > 0
                    else 0 + item["other"]
                    if item["other"] > 0
                    else 0
                ),
            ),
            storage=StorageMix(hydro=item["hydroStorage"] * -1),
            source="someservice.com",
        )
        # Or you can create the production mix and fill it later.
        production_mix = ProductionMix()
        for mode, value in item.items():
            production_mix.add_value(mode, value)
        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(item["datetime"]),
            production=production_mix,
            storage=StorageMix(hydro=item["hydroStorage"] * -1),
            source="someservice.com",
        )
    # For now we should return a list of dictionaries
    # and therefore we convert the ProductionBreakdownList to a list
    # using the to_list() method.
    # In the future we will return a ProductionBreakdownList directly.
    return production_list.to_list()
