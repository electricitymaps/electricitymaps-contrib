#!/usr/bin/env python3
import logging
import datetime
import re

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.

def parse_html(html):
    html = html.replace('\n', ' ').replace('\r', ' ')

    columns = [m.group(1) for m in re.finditer(
        '''data\.addColumn\("number", "([^"]*)"\);''', html)]
    assert columns == ['Συνολική Προβλεπόμενη Ζήτηση', 'Αιολική Παραγωγή',
        'Εκτίμηση Διεσπαρμένης Παραγωγής (Φωτοβολταϊκά και Βιομάζα)',
        'Συνολική Ζήτηση', 'Συμβατική Παραγωγή']

    times = (m.group(1, 2, 3) for m in re.finditer(
        '''var dateStr = "([^"]*)";\s+var hourStr = "(\d+)";\s+var minutesStr = "(\d+)";''', html))
    prods = (m.group(1, 2, 3, 4) for m in re.finditer(
        '''\[\s*dateStrFormat,\s*(\d+|null),\s*(\d+|null),\s*(\d+|null),\s*(\d+|null)\s*\]''', html))

    last_datum = None
    for t, p in zip(times, prods):
        # find last datum without null values
        # this is the current as null is used for where the chart should show estimates
        if any(e == 'null' for e in p):
            break
        last_datum = (t, p)

    if last_datum is None:
        return None
    last_time, last_prods = last_datum

    last_time = last_time[0] + ' ' + last_time[1] + ':' + last_time[2]

    last_prods = {
        'oil': float(last_prods[3]),
        'solar': float(last_prods[1]),
        'wind': float(last_prods[0]),
        'biomass': 6.0 # estimate based on the reported solar+biomass production during the night
    }
    last_prods['solar'] -= last_prods['biomass']
    if (last_prods['solar'] < 0.0):
        last_prods['solar'] = 0.0

    return last_time, last_prods

def fetch_production(zone_key='CY', session=None,
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
    assert zone_key == 'CY'

    r = session or requests.session()
    if target_datetime is None:
        url = 'https://tsoc.org.cy/total-daily-system-generation-on-the-transmission-system/'
    else:
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        # url_date = arrow.get(target_datetime).to(
        #     "America/Argentina/Buenos_Aires")
        # url = 'https://api.someservice.com/v1/productionmix/{}'.format(
        #     url_date)

        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(url)
    assert res.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={}'.format(
                                       zone_key, url)

    last_time, last_prods = parse_html(res.text)

    last_time = arrow.get(last_time).replace(tzinfo='Asia/Nicosia')

    data = {
        'zoneKey': zone_key,
        'production': last_prods,
        'storage': {},
        'source': 'tsoc.org.cy',
        'datetime': last_time.datetime
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""

    print('fetch_production() ->')
    print(fetch_production())
