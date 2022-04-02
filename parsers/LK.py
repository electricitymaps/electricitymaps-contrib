#!/usr/bin/env python3

"""Hourly data parser for Sri Lanka
Fetches data for the previous day in 15-minute increment
Data is from the backend for the load curve graph on https://cebcare.ceb.lk/gensum/details
"""

import logging
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
import json
from parsers.lib.exceptions import ParserException

TIMEZONE_NAME = 'Asia/Colombo'
GENERATION_BREAKDOWN_URL = "https://cebcare.ceb.lk/GenSum/GetLoadCurveData"
SOURCE_NAME = "ceb.lk"

def fetch_production(zone_key='LK', session=None, target_datetime=None, logger: logging.Logger = logging.getLogger(__name__)):
  """Requests the last known production mix (in MW) of a given region
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
  if target_datetime is not None and target_datetime < arrow.utcnow().shift(days=-2):
      raise NotImplementedError('The datasource currently only has data for yesterday') # so 0-24 hours ago just after local midnight to approx. 24-48 hours ago just before midnight

  r = session or requests.session()

  response = r.get(GENERATION_BREAKDOWN_URL)

  assert response.status_code == 200, 'Exception when fetching production for ' \
                               '{}: error when calling url={}'.format(
                                   zone_key, GENERATION_BREAKDOWN_URL)

  source_data = json.loads(response.json()) # Response is double encoded; a JSON array encoded as a JSON string

  logger.debug(f"Raw generation breakdown: {source_data}", extra={"key": zone_key})

  output = []

  for quarter_hourly_source_data in source_data:

    output_for_timestamp = {
      'zoneKey': zone_key,
      'datetime': arrow.get(quarter_hourly_source_data['DateTime'], 'YYYY-MM-DD HH:mm:ss', tzinfo=TIMEZONE_NAME).datetime,
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': 0.0,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'source': SOURCE_NAME
    }

    for generation_type, outputInMW in quarter_hourly_source_data.items():
      if(generation_type == "DateTime"):
        continue

      if generation_type == "Coal":
        output_for_timestamp['production']['coal'] += outputInMW
      elif generation_type == "Major Hydro" or generation_type == 'SPP Minihydro':
        output_for_timestamp['production']['hydro'] += outputInMW
      elif generation_type == "SPP Biomass":
        output_for_timestamp['production']['biomass'] += outputInMW
      elif generation_type == "Solar":
        output_for_timestamp['production']['solar'] += outputInMW
      elif generation_type == "Thermal-Oil":
        output_for_timestamp['production']['oil'] += outputInMW
      elif generation_type == "Wind":
        output_for_timestamp['production']['wind'] += outputInMW
      else:
        raise ParserException(zone_key, "Unknown production type: " + generation_type)

    output.append(output_for_timestamp)

  return output

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
