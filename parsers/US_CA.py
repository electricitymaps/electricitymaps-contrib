# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

from datetime import datetime, timedelta


def fetch_production(country_code='FR', session=None):
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
    s = requests.session()
    yesterday = datetime.now() - timedelta(days=1)
    url = 'https://content.caiso.com/green/renewrpt/' + yesterday.strftime('%Y%m%d')  +'_DailyRenewablesWatch.txt'
    print url
    response = s.get(url)
    obj = response.text.splitlines()

    res = {}
    res['countryCode'] = 'US_CA'
    res['datetime'] = datetime.now()
    res['production'] = {}
    res['production']['biomass'] = int(obj[2].split('\t')[5])
    res['production']['gas'] = int(obj[2].split('\t')[7])
    # hydro + small hydro
    res['production']['hydro'] = int(obj[2].split('\t')[9]) + int(obj[30].split('\t')[11])
    res['production']['nuclear'] = int(obj[30].split('\t')[5])
    # solar PV + thermal
    res['production']['solar'] = int(obj[2].split('\t')[13]) + int(obj[2].split('\t')[15])
    res['production']['wind'] = int(obj[2].split('\t')[11])
    res['production']['geothermal'] = int(obj[2].split('\t')[3])
    res['production']['unknown'] = int(obj[2].split('\t')[5])

    print res

      # item # 2 -> 26
      #- GEOTHERMAL: 3
      #- BIOMASS: 5
      #- BIOGAS: 7
      #- SMALL HYDRO: 9
      #- WIND TOTAL: 11
      #- SOLAR PV: 13
      #- SOLAR THERMAL: 15 
      # item # 30 -> 55 
      #x RENEWABLES : 3 
      #- NUCLEAR : 5
      #x THERMAL : 7
      #x IMPORTS : 9
      #- HYDRO : 11


    data = {
        'countryCode': country_code,
        'production': {},
        'storage': {},
        'source': 'someservice.com',
    }
    for item in obj['productionMix']:
        # All production values should be >= 0
        data['production'][item['key']] = item['value'] # Should be a floating point value

    for item in obj['storage']:
        # Positive storage means energy is stored
        # Negative storage means energy is generated from the storage system
        data['storage'][item['key']] = item['value'] # Should be a floating point value

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data



def fetch_price(country_code='FR', session=None):
    """Requests the last known power price of a given country

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    """

    r = session or requests.session()
    url = 'https://api.someservice.com/v1/price/latest'
    response = r.get(url)
    obj = response.json()

    data = {
        'countryCode': country_code,
        'currency': 'EUR',
        'price': obj['price'],
        'source': 'someservice.com',
    }

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


def fetch_exchange(country_code1='DK', country_code2='NO', session=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """

    r = session or requests.session()
    url = 'https://api.someservice.com/v1/exchange/latest?from=%s&to=%s' % (country_code1, country_code2)
    response = r.get(url)
    obj = response.json()

    data = {
        'sortedCountryCodes': '->'.join(sorted([country_code1, country_code2])),
        'source': 'someservice.com',
    }

    # Country codes are sorted in order to enable easier indexing in the database
    sorted_country_codes = sorted([country_code1, country_code2])
    # Here we assume that the net flow returned by the api is the flow from 
    # country1 to country2. A positive flow indicates an export from country1
    # to country2. A negative flow indicates an import.
    netFlow = obj['exchange']
    # The net flow to be reported should be from the first country to the second
    # (sorted alphabetically). This is NOT necessarily the same direction as the flow
    # from country1 to country2
    data['netFlow'] = netFlow if country_code1 == sorted_country_codes[0] else -1 * netFlow

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
    print 'fetch_price() ->'
    print fetch_price()
    print 'fetch_exchange(DK, NO) ->'
    print fetch_exchange('DK', 'NO')
