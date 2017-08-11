import arrow
import requests
from bs4 import BeautifulSoup
import re


def fetch_total_and_wind_production(session = None):
    r = session or requests.session()
    url = 'http://www.dsm.org.cy/en/daily-system-generation-on-the-transmission-system-mw/total-daily-system-generation-mw'
    response = r.get(url)
    html = response.text    # we have an html page from the url above that contains the raw data for the generation table
    soup = BeautifulSoup(html, 'html.parser')

    # first we ensure the column headers are what we expect, otherwise we will be notified
    header = soup.find_all('tr')[0].find_all('th')
    if header[0].string != 'Time' or \
        header[1].string != 'Generation Forecast' or \
        header[2].string != 'Actual Generation (MW)' or \
        header[3].string != 'Total Available Generation Capacity' or \
        header[4].string != 'Wind Farms Generation':
        raise Exception('Mapping for Cyprus has changed')

    # now we can parse the table to find the last line that is written, this the values we're looking for
    rows = soup.find_all('tr')[1:]
    time = None
    actual = None
    wind = None
    for row in rows:
        cols = row.find_all('td')
        try:
            actual = float(cols[2].string)
            wind = float(cols[4].string)
            time = cols[0].string
        except (TypeError, ValueError):
            pass    # we should end up with the last populated value

    return time, actual, wind


def fetch_solar_production_estimation(session = None):
    r = session or requests.session()
    url = 'http://www.dsm.org.cy/en/objects/reusable-objects/daily-wind-and-solar-farms-generation-mw'
    response = r.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    solar = None

    # this is getting ugly, we are searching for the javascript code of the page used to draw the chart
    # solar data is estimated and doesn't appear on the xls on their website
    script = soup.find_all(string=re.compile('google\.visualization\.DataTable'))
    if len(script) > 0:
        # in the js code we search fo the point values
        res = re.findall('data\.addRows\((.*)\)', script[0])
        if res:
            res = str(res[0]).split('],[')
            # res is now a list of results like below containing [hour, minute, second, wind, solar]
            # [0,45,00],5,0
            # [1,0,00],7,0
            # [1,15,00],null,null
        if res:
            for row in res:
                cols = row.split(',')
                # cols is now a list like [0,45,0,5,0], containing [hour, minute, second, wind, solar]
                try:
                    solar = float(cols[4])
                except (TypeError, ValueError):
                    pass  # we should end up with the last populated value
    return solar


def fetch_production(country_code='CY', session=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
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

    time, total, wind = fetch_total_and_wind_production()
    solar = fetch_solar_production_estimation()

    data = {
        'countryCode': country_code,
        'production': {},
        'storage': {},
        'source': 'http://www.dsm.org.cy',
    }
    if solar is not None and solar >= 0:
        data['production']['solar'] = solar
        if total:
            total -= solar
    if wind is not None and wind >= 0:
        data['production']['wind'] = wind
        if total:
            total -= wind
    if total is not None and total >= 0:
        # as discussed in issue 122 on github, put all the non wind/solar as unknown.
        # It will be assigned a "fossil fuel" co2 emission intensity.
        data['production']['unknown'] = total

    # Parse the datetime and return a python datetime object
    hour = int(time.split(':')[0])
    minute = int(time.split(':')[1])
    data['datetime'] = arrow.now('Europe/Nicosia').floor('day').replace(hour=hour, minute=minute)

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
