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
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
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
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
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
      'zoneKey': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    or a list of dictionaries in the form:
    [
      {
        'zoneKey': 'FR',
        'currency': EUR,
        'datetime': '2017-01-01T00:00:00Z',
        'price': 0.0,
        'source': 'mysource.com'
      },
      {
        'zoneKey': 'FR',
        'currency': EUR,
        'datetime': '2017-01-01T01:00:00Z',
        'price': 0.0,
        'source': 'mysource.com'
      },
      ...
    ]
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    url = "https://api.someservice.com/v1/price/latest"

    response = session.get(url)
    assert (
        response.status_code == 200
    ), f"Exception when fetching price for {zone_key}: error when calling url={url}"

    obj = response.json()

    data = {
        "zoneKey": zone_key,
        "datetime": datetime.fromisoformat(obj["datetime"]),
        "currency": "EUR",
        "price": obj["price"],
        "source": "someservice.com",
    }

    return data


def fetch_exchange(
    zone_key1: str = "DK",
    zone_key2: str = "NO",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    """
    Requests the last known power exchange (in MW) between two countries.

    Arguments:
    ----------
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not
      provided, we should default it to now. If past data is not available,
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
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
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    or a list of dictionaries in the form:
    [
      {
        'sortedZoneKeys': 'DK->NO',
        'datetime': '2017-01-01T00:00:00Z',
        'netFlow': 0.0,
        'source': 'mysource.com'
      },
      {
        'sortedZoneKeys': 'DK->NO',
        'datetime': '2017-01-01T01:00:00Z',
        'netFlow': 0.0,
        'source': 'mysource.com'
      },
      ...
    ]
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or Session()
    url = "https://api.someservice.com/v1/exchange/latest?" "from={}&to={}".format(
        zone_key1, zone_key2
    )

    response = r.get(url)
    assert response.status_code == 200
    obj = response.json()

    data = {
        "sortedZoneKeys": "->".join(sorted([zone_key1, zone_key2])),
        "source": "someservice.com",
    }

    # Zone keys are sorted in order to enable easier indexing in the database
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    # Here we assume that the net flow returned by the api is the flow from
    # country1 to country2. A positive flow indicates an export from country1
    # to country2. A negative flow indicates an import.
    net_flow = obj["exchange"]
    # The net flow to be reported should be from the first country to the
    # second (sorted alphabetically). This is NOT necessarily the same
    # direction as the flow from country1 to country2
    data["netFlow"] = net_flow if zone_key1 == sorted_zone_keys[0] else -1 * net_flow

    # Parse the datetime and return a python datetime object
    data["datetime"] = arrow.get(obj["datetime"]).datetime

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    print("fetch_exchange(DK, NO) ->")
    print(fetch_exchange("DK", "NO"))
