
import logging
import datetime

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

from __future__ import annotations

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def fetch_production(zone_key='GB-SHI', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)) -> dict:
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
    data = {
      'zoneKey': zone_key,
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'gas': 0.0,
          'oil': 0.0,
          'wind': 0.0
      },
      'capacity': {
          'gas': 15,
          'oil': 67,
          'wind': 3.68,
      },
      'storage': {
          'hydro': 0,
      },
      'source': 'https://www.ssen.co.uk/WorkArea/DownloadAsset.aspx?id=3833'
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
