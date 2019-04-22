def fetch_production(zone_key='PH', session=None, target_datetime=None, logger=None):
    return {
      'countryCode': 'PH',
      'datetime': '2018-12-31T00:00:00Z',
      'production': {
          'biomass': 1.1,
          'coal': 52.0,
          'gas': 21.4,
          'hydro': 9.4,
          'nuclear': None,
          'oil': 3.2,
          'solar': 1.3,
          'wind': 1.2,
          'geothermal': 10.5,
          'unknown': 0.0
      },
      'storage': {
      },
      'source': 'https://www.doe.gov.ph/sites/default/files/pdf/energy_statistics/01_2018_power_statistics_as_of_29_march_2019_summary.pdf'
    }
