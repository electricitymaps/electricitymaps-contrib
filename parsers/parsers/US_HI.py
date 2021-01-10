#!/usr/bin/env python3

import logging
import datetime
import arrow
import requests


def fetch_production(zone_key='US-HI-OA', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    """Requests the last known production mix (in MW) of a given country

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
    """
    r = session or requests.session()
    if target_datetime is None:
        url_date = arrow.get()
        url = 'https://www.islandpulse.org/api/mix?limit=1'
    else:
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        #url_date = arrow.get(target_datetime).to("Pacific/Honolulu")
        #url = 'https://www.islandpulse.org/api/mix?date={}'.format(url_date.date())

        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(url)

    obj = res.json()
    raw_data = obj[0]

    production = {
          'biomass': float(raw_data['Waste2Energy'] + raw_data['BioFuel']),
          'coal': float(raw_data['Coal']),
          'oil': float(raw_data['Fossil_Fuel']),
          'solar': float(raw_data['Solar']),
          'wind': float(raw_data['WindFarm'])
    }

    dt = arrow.get(raw_data['dateTime']).to(tz="Pacific/Honolulu").datetime

    data = {
        'zoneKey': zone_key,
        'production': production,
        'datetime': dt,
        'storage': {},
        'source': 'islandpulse.org'
    }

    return data

if __name__ == '__main__':
    print("fetch_production ->")
    print(fetch_production())
