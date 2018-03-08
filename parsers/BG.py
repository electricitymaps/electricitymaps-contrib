#!/usr/bin/env python3
# coding=utf-8

import arrow
from bs4 import BeautifulSoup
import requests

TYPE_MAPPING = {                        # Real values around midnight
    u'АЕЦ': 'nuclear',                  # 2000
    u'Кондензационни ТЕЦ': 'coal',      # 1800
    u'Топлофикационни ТЕЦ': 'gas',      # 146
    u'Заводски ТЕЦ': 'gas',             # 147
    u'ВЕЦ': 'hydro',                    # 7
    u'Малки ВЕЦ': 'hydro',              # 74
    u'ВяЕЦ': 'wind',                    # 488
    u'ФЕЦ': 'solar',                    # 0
    u'Био ТЕЦ': 'biomass',              # 29
    u'Товар РБ': 'consumption',         # 3175
}


def time_string_converter(ts):
    """Converts time strings into aware datetime objects."""

    dt_naive = arrow.get(ts, 'DD.MM.YYYY HH:mm:ss')
    dt_aware = dt_naive.replace(tzinfo='Europe/Sofia').datetime

    return dt_aware


def fetch_production(zone_key='BG', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
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
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'http://www.eso.bg/?did=124'
    response = r.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    try:
        time_div = soup.find("div", {"class": "dashboardCaptionDiv"})
        bold = time_div.find('b')
    except AttributeError:
        raise LookupError('No data currently available for Bulgaria.')

    time_string = bold.string
    dt = time_string_converter(time_string)

    table = soup.find("table", {"class": "defaultTable2"})
    rows = table.findChildren("tr")

    datapoints = []
    for row in rows[1:-1]:
        gen_tag = row.find("td")
        gen = gen_tag.text
        val_tag = gen_tag.findNext("td")
        val = float(val_tag.find("b").text)
        datapoints.append((TYPE_MAPPING[gen], val))

    production = {}
    for k, v in datapoints:
        production[k] = production.get(k, 0.0) + v

    data = {
        'zoneKey': zone_key,
        'production': production,
        'storage': {},
        'source': 'eso.bg',
        'datetime': dt
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
