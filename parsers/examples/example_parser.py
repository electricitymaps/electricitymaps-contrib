from datetime import datetime
from logging import Logger, getLogger
from typing import List, Optional, Union

from pytz import timezone

# The request library is used to fetch content through HTTP
from requests import Response, Session

from parsers.lib.exceptions import ParserException


def fetch_production(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
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
      `target_datetime = target_datetime.astimezone(tz=timezone('America/New_York'))`.
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

    A dictionary in the form:
    {
      'zoneKey': 'XX',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    or a list of dictionaries in the form:
    [
      {
        'zoneKey': 'XX',
        'datetime': '2017-01-01T00:00:00Z',
        'production': {
            'biomass': 0.0,
            'coal': 0.0,
            'gas': 0.0,
            'hydro': 0.0,
            'nuclear': null,
            'oil': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': 0.0
        },
        'storage': {
            'hydro': -10.0,
        },
        'source': 'mysource.com'
      },
      {
        'zoneKey': 'XX',
        'datetime': '2017-01-01T01:00:00Z',
        'production': {
            'biomass': 0.0,
            'coal': 0.0,
            'gas': 0.0,
            'hydro': 0.0,
            'nuclear': null,
            'oil': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': 0.0
        },
        'storage': {
            'hydro': -10.0,
        },
        'source': 'mysource.com'
      },
      ...
    ]
    """
    if target_datetime is None:
        url = "https://api.someservice.com/v1/productionmix/latest"
    elif target_datetime > datetime(year=2000, month=1, day=1):
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        url_date = target_datetime.astimezone(
            timezone("America/Argentina/Buenos_Aires")
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
    assert (
        res.status_code == 200
    ), f"Exception when fetching production for {zone_key}: error when calling url={url}"

    obj = res.json()

    production_data_list: List[dict] = []
    for item in obj["productionMix"]:
        production_data_list.append(
            {
                "zoneKey": zone_key,
                "datetime": datetime.fromisoformat(item["datetime"]),
                "production": {
                    "biomass": item["biomass"],
                    "coal": item["coal"],
                    "gas": item["gas"],
                    "hydro": item["hydro"],
                    "nuclear": item["nuclear"],
                    "oil": item["oil"],
                    "solar": item["solar"],
                    "wind": item["wind"],
                    "geothermal": item["geothermal"],
                    "unknown": item["unknown"]
                    if item["unknown"] > 0
                    else 0 + item["other"]
                    if item["other"] > 0
                    else 0,
                },
                "storage": {"hydro": item["hydroStorage"] * -1},
                "source": "someservice.com",
            }
        )

    return production_data_list


def fetch_price(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
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
      `target_datetime = target_datetime.astimezone(tz=timezone('America/New_York'))`.
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

    A dictionary in the form:
    {
      'zoneKey': 'XX',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    or a list of dictionaries in the form:
    [
      {
        'zoneKey': 'XX',
        'currency': EUR,
        'datetime': '2017-01-01T00:00:00Z',
        'price': 0.0,
        'source': 'mysource.com'
      },
      {
        'zoneKey': 'XX',
        'currency': EUR,
        'datetime': '2017-01-01T01:00:00Z',
        'price': 0.0,
        'source': 'mysource.com'
      },
      ...
    ]
    """
    if target_datetime:
        raise ParserException(
            "example_parser.py",
            "This parser is not yet able to parse past dates",
            zone_key,
        )

    url = "https://api.someservice.com/v1/price/latest"

    response = session.get(url)
    assert (
        response.status_code == 200
    ), f"Exception when fetching price for {zone_key}: error when calling url={url}"

    obj = response.json()

    price_list: List[dict] = []

    for item in obj:
        price_list.append(
            {
                "zoneKey": zone_key,
                "currency": "EUR",
                "datetime": datetime.fromisoformat(item["datetime"]),
                "price": item["price"],
                "source": "someservice.com",
            }
        )

    return price_list


def fetch_exchange(
    zone_key1: str = "XX",
    zone_key2: str = "YY",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
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
      `target_datetime = target_datetime.astimezone(tz=timezone('America/New_York'))`.
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

    A dictionary in the form:
    {
      'sortedZoneKeys': 'XX->YY',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    or a list of dictionaries in the form:
    [
      {
        'sortedZoneKeys': 'XX->YY',
        'datetime': '2017-01-01T00:00:00Z',
        'netFlow': 0.0,
        'source': 'mysource.com'
      },
      {
        'sortedZoneKeys': 'XX->YY',
        'datetime': '2017-01-01T01:00:00Z',
        'netFlow': 0.0,
        'source': 'mysource.com'
      },
      ...
    ]
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = f"https://api.someservice.com/v1/exchange/latest"
    params = {
        "from": zone_key1,
        "to": zone_key2,
    }

    response = session.get(url, params=params)
    assert (
        response.status_code == 200
    ), f"Exception when fetching exchange for {zone_key1} -> {zone_key2}: error when calling url={url}"
    obj = response.json()

    exchange_list: List[dict] = []

    for item in obj:
        exchange_list.append(
            {
                # Zone keys are sorted in order to enable easier indexing in the database
                "sortedZoneKeys": "->".join(sorted([zone_key1, zone_key2])),
                # Parse the datetime and return a python datetime object
                "datetime": datetime.fromisoformat(item["datetime"]),
                # Here we assume that the net flow returned by the api is the flow from
                # country1 to country2. A positive flow indicates an export from country1
                # to country2. A negative flow indicates an import.
                "netFlow": item["exchange"],
                "source": "someservice.com",
            }
        )

    return exchange_list


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print("fetch_production(XX) ->")
    print(fetch_production("XX"))
    print("fetch_price(XX) ->")
    print(fetch_price("XX"))
    print("fetch_exchange(XX, YY) ->")
    print(fetch_exchange("XX", "YY"))
