from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

# The request library is used to fetch content through HTTP
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException


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
        url = "https://api.someservice.com/v1/productionmix/latest"
    elif target_datetime > datetime(year=2000, month=1, day=1):
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        url_date = target_datetime.astimezone(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ).strftime("%Y-%m-%d")
        url = f"https://api.someservice.com/v1/productionmix/{url_date}"
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise ParserException(
            "example_parser.py",
            "This parser is not yet able to parse dates before 2000-01-01",
            zone_key,
        )

    res: Response = session.get(url)
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
                unknown=item["unknown"]
                if item["unknown"] > 0
                else 0 + item["other"]
                if item["other"] > 0
                else 0,
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


def fetch_price(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """
    Requests the last known power price of a given country.

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
      changed or is not available, raise an Exception.
    Returns a PriceList containing all price events.
    """
    if target_datetime:
        raise ParserException(
            "example_parser.py",
            "This parser is not yet able to parse past dates",
            zone_key,
        )

    url = "https://api.someservice.com/v1/price/latest"

    response = session.get(url)
    if not response.ok:
        raise ParserException(
            "example_parser.py",
            f"Exception when fetching price error code: {response.status_code}: {response.text}",
            zone_key,
        )

    obj = response.json()

    price_list = PriceList(logger=logger)

    for item in obj:
        price_list.append(
            zoneKey=zone_key,
            currency="EUR",
            datetime=datetime.fromisoformat(item["datetime"]),
            price=item["price"],
            source="someservice.com",
        )
    # For now we should return a list of dictionaries
    # and therefore we convert the PriceList to a list
    # using the to_list() method.
    # In the future we will return a PriceList directly.
    return price_list.to_list()


def fetch_exchange(
    zone_key1: ZoneKey = ZoneKey("XX"),
    zone_key2: ZoneKey = ZoneKey("YY"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """
    Requests the last known power exchange (in MW) between two countries.

    Arguments:
    ----------
    zone_key1: used is used to identify the first zone of a exchange pair.
    zone_key2: used is used to identify the second zone of a exchange pair.
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
      changed or is not available, raise an Exception.

    Returns an ExchangeList containing all exchange events.
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = "https://api.someservice.com/v1/exchange/latest"
    params = {
        "from": zone_key1,
        "to": zone_key2,
    }

    response = session.get(url, params=params)
    if not response.ok:
        raise ParserException(
            "example_parser.py",
            f"Exception when fetching exchange error code: {response.status_code}: {response.text}",
            ZoneKey("->".join(sorted([zone_key1, zone_key2]))),
        )
    obj = response.json()

    exchange_list = ExchangeList(logger=logger)

    for item in obj:
        exchange_list.append(
            # Zone keys are sorted in order to enable easier indexing in the database
            zoneKey=ZoneKey("->".join(sorted([zone_key1, zone_key2]))),
            # Parse the datetime and return a python datetime object
            datetime=datetime.fromisoformat(item["datetime"]),
            # Here we assume that the net flow returned by the api is the flow from
            # country1 to country2. A positive flow indicates an export from country1
            # to country2. A negative flow indicates an import.
            netFlow=item["exchange"],
            source="someservice.com",
        )

    return exchange_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Requests the last known power consumption (in MW) of a given zone.

    Arguments:
    ----------
    zone_key: used is used to identify the zone to which the consumption data
      is related to.
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
      changed or is not available, raise a ParserException.

    Returns a ConsumptionList containing all consumption events.
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = "https://api.someservice.com/v1/consumption/latest"
    params = {
        "zone": zone_key,
    }

    response = session.get(url, params=params)
    if not response.ok:
        raise ParserException(
            "example_parser.py",
            f"Exception when fetching consumption error code: {response.status_code}: {response.text}",
            zone_key,
        )
    obj = response.json()

    consumption_list = TotalConsumptionList(logger=logger)

    for item in obj:
        consumption_list.append(
            zoneKey=zone_key,
            # Parse the datetime and return a python datetime object
            datetime=datetime.fromisoformat(item["datetime"]),
            consumption=item["consumption"],
            source="someservice.com",
        )
    return consumption_list.to_list()


def fetch_total_production(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict | list[dict]:
    """
    Requests the last known power production (in MW) of a given zone.

    Arguments:
    ----------
    zone_key: used is used to identify the zone to which the production data
      is related to.
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
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = "https://api.someservice.com/v1/production/latest"
    params = {
        "zone": zone_key,
    }

    response = session.get(url, params=params)
    if not response.ok:
        raise ParserException(
            "example_parser.py",
            f"Exception when fetching total production error code: {response.status_code}: {response.text}",
            zone_key,
        )
    obj = response.json()

    production_list = TotalProductionList(logger=logger)

    for item in obj:
        production_list.append(
            zoneKey=zone_key,
            # Parse the datetime and return a python datetime object
            datetime=datetime.fromisoformat(item["datetime"]),
            value=item["production"],
            source="someservice.com",
        )
    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print("fetch_production(XX) ->")
    print(fetch_production(ZoneKey("XX")))
    print("fetch_price(XX) ->")
    print(fetch_price(ZoneKey("XX")))
    print("fetch_exchange(XX, YY) ->")
    print(fetch_exchange(ZoneKey("XX"), ZoneKey("YY")))
    print("fetch_consumption(XX) ->")
    print(fetch_consumption(ZoneKey("XX")))
    print("fetch_total_production(XX) ->")
    print(fetch_total_production(ZoneKey("XX")))
