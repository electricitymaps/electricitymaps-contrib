# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests


def fetch_production(country_code='SE', session=None):
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
    r = session or requests.session()
    timestamp = arrow.now().timestamp * 1000
    url = 'http://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview?timestamp=%d' % timestamp
    response = r.get(url)
    obj = response.json()

    data = {
        'countryCode': country_code,
        'production': {
          'nuclear': float(filter(
            lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Nuclear', country_code),
            obj['NuclearData'])[0]['value'].replace(u'\xa0', '')),
          'hydro': float(filter(
            lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Hydro', country_code),
            obj['HydroData'])[0]['value'].replace(u'\xa0', '')),
          'wind': float(filter(
            lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Wind', country_code),
            obj['WindData'])[0]['value'].replace(u'\xa0', '')),
          'unknown':
            float(filter(
              lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Thermal', country_code),
              obj['ThermalData'])[0]['value'].replace(u'\xa0', '')) +
            float(filter(
              lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('NotSpecified', country_code),
              obj['NotSpecifiedData'])[0]['value'].replace(u'\xa0', '')),
        },
        'storage': {},
        'source': 'driftsdata.stattnet.no',
    }

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['MeasuredAt'] / 1000).datetime

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production(SE) ->'
    print fetch_production('SE')
