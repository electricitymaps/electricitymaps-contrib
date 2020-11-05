#!/usr/bin/env python3
import logging
import datetime
import re

# Tablib is used to parse XLSX files
import tablib
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def fetch_production(zone_key='XK', session=None,
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
        url = 'https://www.kostt.com/Content/ViewFiles/Transparency/BasicMarketDataOnGeneration/Prodhimi%20aktual%20gjenerimi%20faktik%20i%20energjise%20elektrike.xlsx'
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(url)
    assert res.status_code == 200, 'XK (Kosovo) parser: GET {} returned {}'.format(url, res.status_code)

    sheet = tablib.Dataset().load(res.content, headers=False)

    productions = {} # by time
    for i in range(5, 1000):
        try:
            row = sheet[i]
        except IndexError:
            break
        time = row[1]
        if time is None:
            break
        if isinstance(time, float):
            time = datetime.time(hour=round(time * 24) % 24)
        time_str = time.strftime('%H:%M')
        assert 'TC KOSOVA' in row[3], 'Parser assumes only coal data'
        prod = float(row[2])
        productions[time_str] = productions.get(time_str, 0.0) + prod

    date_match = re.search(r'ACTUAL\s+GENERATION\s+FOR\s+DAY\s+(\d+)\.(\d+)\.(\d+)', sheet[1][1])
    assert date_match is not None, 'Date not found in spreadsheet'
    date_str = date_match.group(3) + '-' + date_match.group(2) + '-' + date_match.group(1) + ' '

    data = []
    for time_str, prod in productions.items():
        timestamp = arrow.get(date_str + time_str).replace(tzinfo='Europe/Belgrade')
        timestamp = timestamp.shift(hours=-1) # shift to start of period
        if time_str == '00:00':
            # Based on the apparent discontinuity in production and the order in the spreadsheet
            # it seems that the last data-point belongs to the next day
            timestamp = timestamp.shift(days=1)
        data.append({
            'zoneKey': zone_key,
            'production': {
                'coal': prod
            },
            'storage': {},
            'source': 'kostt.com',
            'datetime': timestamp.datetime
        })

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""

    print('fetch_production() ->')
    for datum in fetch_production():
        print(datum)
