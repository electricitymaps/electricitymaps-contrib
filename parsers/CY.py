#!/usr/bin/env python3
import logging
import datetime
import re
import sys

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def append_datum(data, time_str, prods_str):
    time_str = time_str[0] + ' ' + time_str[1] + ':' + time_str[2]
    time_value = arrow.get(time_str).replace(tzinfo='Asia/Nicosia').datetime

    prods_value = {
        'oil': float(prods_str[3]),
        'solar': float(prods_str[1]),
        'wind': float(prods_str[0]),
        'biomass': 0.0
    }

    # Because solar is explicitly listed as "Solar PV" (so no thermal with energy storage) and there
    # is zero sunlight in the middle of the night (https://www.timeanddate.com/sun/cyprus/nicosia),
    # we use the biomass+solar generation reported at 0:00 to determine the portion of biomass+solar
    # which constitutes biomass
    nocturnal_biomass_generation = data[0]['production']['biomass'] if len(data) != 0 else prods_value['solar']
    prods_value['solar'] -= nocturnal_biomass_generation
    prods_value['biomass'] += nocturnal_biomass_generation
    if prods_value['solar'] < 0.0:
        # if there is (next to) no sunlight and biomass is lower than at midnight
        prods_value['solar'] = 0.0

    data.append({
        'zoneKey': 'CY',
        'production': prods_value,
        'storage': {},
        'source': 'tsoc.org.cy',
        'datetime': time_value
    })


def parse_html(html):
    html = html.replace('\n', ' ').replace('\r', ' ')

    columns = [m.group(1) for m in re.finditer(
        '''data\.addColumn\("number", "([^"]*)"\);''', html)]
    assert columns == ['Συνολική Προβλεπόμενη Ζήτηση', 'Αιολική Παραγωγή',
        'Εκτίμηση Διεσπαρμένης Παραγωγής (Φωτοβολταϊκά και Βιομάζα)',
        'Συνολική Ζήτηση', 'Συμβατική Παραγωγή'], 'Source format changed'

    times = (m.group(1, 2, 3) for m in re.finditer(
        '''var dateStr = "([^"]*)";\s+var hourStr = "(\d+)";\s+var minutesStr = "(\d+)";''', html))
    prods = (m.group(1, 2, 3, 4) for m in re.finditer(
        '''\[\s*dateStrFormat,\s*(\d+|null),\s*(\d+|null),\s*(\d+|null),\s*(\d+|null)\s*\]''', html))

    data = []
    for t, p in zip(times, prods):
        if any(e == 'null' for e in p):
            break
        append_datum(data, t, p)

    return data


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
        # convert target datetime to local datetime
        url_date = arrow.get(target_datetime).to('Asia/Nicosia')
        url = 'https://tsoc.org.cy/archive-total-daily-system-generation-on-the-transmission-system/?startdt={}&enddt=%2B1days'.format(
            url_date.format('DD-MM-YYYY'))

    res = r.get(url)
    assert res.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={}'.format(
                                       zone_key, url)

    data = parse_html(res.text)

    if len(data) == 0:
        raise Warning('No data returned')

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""

    target_datetime = None
    if len(sys.argv) == 4:
        target_datetime = datetime.datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

    print('fetch_production() ->')
    for datum in fetch_production(target_datetime=target_datetime):
        print(datum)
