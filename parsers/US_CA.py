# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import pandas


def fetch_production(country_code='US-CA', session=None):
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
    # get a clean date at the beginning of yesterday
    yesterday = arrow.utcnow().to('US/Pacific').shift(days=-1).replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    url = 'http://content.caiso.com/green/renewrpt/' + yesterday.format('YYYYMMDD') +'_DailyRenewablesWatch.txt'

    renewableResources = pandas.read_table(url, sep='\t\t', skiprows=2, header=None, names=['Hour', 'GEOTHERMAL','BIOMASS', 'BIOGAS', 'SMALL HYDRO','WIND TOTAL', 'SOLAR PV', 'SOLAR THERMAL'], skipfooter=27, skipinitialspace=True, engine='python')
    otherResources = pandas.read_table(url, sep='\t\t', skiprows=30, header=None, names=['Hour', 'RENEWABLES', 'NUCLEAR', 'THERMAL', 'IMPORTS', 'HYDRO'], skipinitialspace=True, engine='python')

    dailyData = []

    for i in range(0, 24):
        data = {
            'countryCode': country_code,
            'production': {},
            'storage': {},
            'source': 'caiso.com',
        }
        data['production'] = {}
        data['production']['biomass'] = renewableResources['BIOMASS'][i]
        data['production']['gas'] = renewableResources['BIOGAS'][i]
        data['production']['hydro'] = renewableResources['SMALL HYDRO'][i] + otherResources['HYDRO'][i]
        data['production']['nuclear'] = otherResources['NUCLEAR'][i]
        data['production']['solar'] = renewableResources['SOLAR PV'][i] + renewableResources['SOLAR THERMAL'][i]
        data['production']['wind'] = renewableResources['WIND TOTAL'][i]
        data['production']['geothermal'] = renewableResources['GEOTHERMAL'][i]
        data['production']['unknown'] = otherResources['THERMAL'][i] # this is not specified in the list
        # set the date at the end of the hour
        data['datetime'] = yesterday.shift(hours = i+1).datetime
        dailyData.append(data)

    return dailyData


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
