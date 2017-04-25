import arrow
from pyiso import BALANCING_AUTHORITIES, client_factory

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
    'wind': 'wind',
    'other': 'unknown'
}

# Note: the list of ISOs is taken from https://github.com/WattTime/pyiso/blob/master/pyiso/__init__.py#L20
# in order to instantiate every possible client
ISO_LIST = {}
# Get a unique list of balancing authorities such that each (module, client) pair is unique
for k, v in BALANCING_AUTHORITIES.iteritems():
    # We obivously exclude the EU
    if k == 'EU': continue
    # Those clients are not working:
    if v['class'] in ['NVEnergyClient', 'SPPClient']: continue
    ISO_LIST[v['class'] + v['module']] = k
ISO_LIST = ISO_LIST.values()

def fetch_production(country_code='US', session=None):
    obj = {
        'countryCode': country_code,
        'production': {},
        'source': 'github.com/WattTime/pyiso'
    }
    for iso in ISO_LIST:
        cli = client_factory(iso)
        for item in cli.get_generation(latest=True):
            # Set datetime
            # TODO: Check that datetime is not too old compared to now
            if not 'datetime' in obj:
                obj['datetime'] = arrow.get(item['timestamp']).datetime
            else:
                obj['datetime'] = max(obj['datetime'], arrow.get(item['timestamp']).datetime)
            
            fuel_name = item['fuel_name']
            if not fuel_name in MAP_FUEL_NAME:
                # print 'Warning: %s (%s MW) in %s is an unknown fuel type' % (fuel_name, item['gen_MW'], iso)
                key = 'unknown'
                pass
            else:
                # print '%s in %s: %s MW' % (fuel_name, iso, item['gen_MW'])
                key = MAP_FUEL_NAME[fuel_name]
            obj['production'][key] = obj['production'].get(key, 0.0) + item['gen_MW']
    return obj

if __name__ == '__main__':
    print fetch_production()
