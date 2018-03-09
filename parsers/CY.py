#!/usr/bin/env python3

import arrow
import requests
from bs4 import BeautifulSoup
import re

try:
    xrange          # Python 2
except NameError:
    xrange = range  # Python 3


def fetch_total_and_wind_production(session=None):
    """Returns an array that contains [time, total production, wind production] like below
        ['00:00', 689.0, 18.0],
        ['00:15', 680.0, 17.0],
        ['00:30', 673.0, 12.0]
    """
    r = session or requests.session()
    url = 'http://www.dsm.org.cy/en/daily-system-generation-on-the-transmission-system-mw/total-daily-system-generation-mw'
    response = r.get(url)
    html = response.text    # we have an html page from the url above that contains the raw data for the generation table
    soup = BeautifulSoup(html, 'html.parser')

    # first we ensure the column headers are what we expect, otherwise exception
    header = soup.find_all('tr')[0].find_all('th')
    if (header[0].string != 'Time' or
            header[1].string != 'Generation Forecast' or
            header[2].string != 'Actual Generation (MW)' or
            header[3].string != 'Total Available Generation Capacity' or
            header[4].string != 'Wind Farms Generation'):
        raise Exception('Mapping for Cyprus has changed')

    # now we can parse the table to find all the lines that contain actual and wind values
    rows = soup.find_all('tr')[1:]
    res = []
    for row in rows:
        cols = row.find_all('td')
        try:
            time = cols[0].string
            actual = float(cols[2].string)
            wind = float(cols[4].string)
            res.append([time, actual, wind])
        except (TypeError, ValueError):
            pass    # this ensure we read only the columns we have actual and wind production

    return res


def fetch_solar_production_estimation(session=None):
    """
    returns an array that contains [time, solar], like the following
        ['0:0', 0.0]
        ['0:15', 0.0]
        ['0:30', 0.0]
    """
    r = session or requests.session()
    url = 'http://www.dsm.org.cy/en/objects/reusable-objects/daily-wind-and-solar-farms-generation-mw'
    response = r.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    res = []

    # this is getting ugly, we are searching for the javascript code of the page used to draw the chart
    # solar data is estimated and doesn't appear on the xls on their website
    script = soup.find_all(string=re.compile('google\.visualization\.DataTable'))
    if len(script) > 0:
        # in the js code we search fo the point values
        data_pts = re.findall('data\.addRows\((.*)\)', script[0])
        if data_pts:
            data_pts = str(data_pts[0]).split(',')  # split all the elements in the list
            data_pts = [d.replace(']', '').replace('[', '').replace('null', '') for d in data_pts]  # remove useless
            data_pts = [data_pts[i:i + 5] for i in xrange(0, len(data_pts), 5)]         # group the elements 5 by 5
            # data_pts is now a list like below containing [hour, minute, second, wind, solar]
            # ['1', '45', '00', '5', '0'],
            # ['2', '0', '00', '4', '0'],
            # ['2', '15', '00', '', '']
            for point in data_pts:
                try:
                    time = str(point[0]) + ':' + str(point[1])
                    solar = float(point[4])
                    res.append([time, solar])
                except (TypeError, ValueError):
                    pass  # we should end up only with values where solar is populated
    return res


def merge_production(total_and_wind, solar):
    """ Merge the two productions, we assume the prod2 array can be empty or missing or have additional values
    we will also return only the times present on prod1 array

    Arguments
    prod1: contains [time, total, wind]
        ['00:00', 689.0, 18.0],
        ['00:15', 680.0, 17.0],
        ['00:30', 673.0, 12.0]

    prod2: contains [time, solar]
        ['0:0', 0.0]
        ['0:15', 0.0]
        ['0:30', 0.0]
    """

    # first we create a result dict (res) that will contain {time: total, wind}
    res = dict()
    for v in total_and_wind:
        hour = int(v[0].split(':')[0])
        minute = int(v[0].split(':')[1])
        res[arrow.now('Europe/Nicosia').floor('day').replace(hour=hour, minute=minute)] = {
            'total': v[1],
            'wind': v[2]
        }

    # then we create an temporary dict (res2) that contains {time: solar}
    res2 = dict()
    for v in solar:
        hour = int(v[0].split(':')[0])
        minute = int(v[0].split(':')[1])
        res2[arrow.now('Europe/Nicosia').floor('day').replace(hour=hour, minute=minute)] = {
            'solar': v[1],
        }

    # then we browse the result dict and see if the temporary set contains the same time, if yes we merge
    for r in res:
        if r in res2:
            res[r]['solar'] = res2[r]['solar']

    return res


def fetch_production(zone_key='CY', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    An array of dictionary in the form:
    [{
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
    }]
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    total_and_wind_production = fetch_total_and_wind_production()               # [time, total, wind]
    solar_production = fetch_solar_production_estimation()                      # [time, solar]
    production = merge_production(total_and_wind_production, solar_production)  # merge the two arrays

    data = []
    for time in production:
        data.append({
            'zoneKey': zone_key,
            'production': {
                'solar': production[time].get('solar', 0.0),
                'wind': production[time].get('wind', 0.0),
                # as discussed in issue 122 on github, put all the non wind/solar as oil.
                # also, as we only have the total production, we should deduce solar and wind
                'oil': production[time].get('total', 0.0) - production[time].get('solar', 0.0) - production[time].get('wind', 0.0)
            },
            'storage': {},
            'source': 'dsm.org.cy',
            'datetime': time.datetime,
        })

    return sorted(data, key=lambda point: point['datetime'])


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    # print fetch_production()
    res = fetch_production()
    for r in res:
        print(r)
