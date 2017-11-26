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
    # caiso.com provides daily data until the day before today
    s = requests.session()
    yesterday = datetime.now() - timedelta(days=1)
    url = 'https://content.caiso.com/green/renewrpt/' + yesterday.strftime('%Y%m%d')  +'_DailyRenewablesWatch.txt'

    response = s.get(url)
    obj = response.text.splitlines()

    dailyData = []

    for i in range(0, 24):
        data = {
            'countryCode': country_code,
            'production': {},
            'storage': {},
            'source': 'content.caiso.com',
        }
        data['countryCode'] = 'US_CA'
        data['datetime'] = datetime.now()
        data['production'] = {}
        data['production']['biomass'] = int(obj[i+2].split('\t')[5])
        data['production']['gas'] = int(obj[i+2].split('\t')[7])   
        data['production']['hydro'] = int(obj[i+2].split('\t')[9]) + int(obj[i+30].split('\t')[11]) # hydro + small hydro
        data['production']['nuclear'] = int(obj[i+30].split('\t')[5])
        data['production']['solar'] = int(obj[i+2].split('\t')[13]) + int(obj[i+2].split('\t')[15]) # solar PV + thermal
        data['production']['wind'] = int(obj[i+2].split('\t')[11])
        data['production']['geothermal'] = int(obj[i+2].split('\t')[3])
        data['production']['unknown'] = int(obj[i+2].split('\t')[5])
        # set the date at the end of the hour and convert UTC-8 (California) to UTC
        dataTime = yesterday.replace(hour = i, minute = 59, second = 0)- timedelta(hours=8)
        data['datetime'] = dataTime.strftime('%Y-%m-%dT%H:%M:%SZ') 
        dailyData.append(data)

    return dailyData



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
    data = {}
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
    data = {}
    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
    print 'fetch_price() ->'
    print fetch_price()
    print 'fetch_exchange(DK, NO) ->'
    print fetch_exchange('DK', 'NO')
