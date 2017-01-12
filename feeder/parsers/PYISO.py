import arrow
from pyiso import client_factory

MAP_FUEL_NAME = {
    'biogas': 'gas',
    'biomass': 'biomass',
    'coal': 'coal',
    'hydro': 'hydro',
    'natgas': 'gas',
    'nuclear': 'nuclear',
    'oil': 'oil',
    'refuse': 'biomass',
    'solar': 'solar',
    'wind': 'wind'
}

def fetch_production(country_code='XX', session=None):
    # This is a test for ISO New England
    isone = client_factory('ISONE')
    obj = {
        'production': {},
        'source': 'iso-ne.com'
    }
    for item in isone.get_generation(latest=True):
        # Set datetime
        if not 'datetime' in obj:
            obj['datetime'] = arrow.get(item['timestamp'])
        elif obj['datetime'] != arrow.get(item['timestamp']):
            raise Exception('All measurements are not taken at the same time')
        obj['production'][MAP_FUEL_NAME[item['fuel_name']]] = \
            obj['production'].get(MAP_FUEL_NAME[item['fuel_name']], 0.0) + item['gen_MW']
    return obj

if __name__ == '__main__':
    print fetch_production()
