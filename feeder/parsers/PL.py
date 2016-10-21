from bs4 import BeautifulSoup
import arrow, requests

COUNTRY_CODE = 'PL'
ENTSOE_ENDPOINT = 'https://transparency.entsoe.eu/api'
ENTSOE_PARAMETER_DESC = {
    'B01': 'Biomass',
    'B02': 'Fossil Brown coal/Lignite',
    'B03': 'Fossil Coal-derived gas',
    'B04': 'Fossil Gas',
    'B05': 'Fossil Hard coal',
    'B06': 'Fossil Oil',
    'B07': 'Fossil Oil shale',
    'B08': 'Fossil Peat',
    'B09': 'Geothermal',
    'B10': 'Hydro Pumped Storage',
    'B11': 'Hydro Run-of-river and poundage',
    'B12': 'Hydro Water Reservoir',
    'B13': 'Marine',
    'B14': 'Nuclear',
    'B15': 'Other renewable',
    'B16': 'Solar',
    'B17': 'Waste',
    'B18': 'Wind Offshore',
    'B19': 'Wind Onshore',
    'B20': 'Other',
}
ENTSOE_PARAMETER_BY_DESC = {v: k for k, v in ENTSOE_PARAMETER_DESC.iteritems()}

session = requests.session()

def query(psr_type):
    now = arrow.utcnow()
    params = {
        'psrType': psr_type,
        'documentType': 'A75',
        'processType': 'A16',
        'in_Domain': '10YPL-AREA-----S',
        'periodStart': now.replace(hours=-24).format('YYYYMMDDHH00'),
        'periodEnd': now.replace(hours=+24).format('YYYYMMDDHH00'),
        'securityToken': '7466690c-c66a-4a00-8e21-2cb7d538f380'
    }
    response = session.get(ENTSOE_ENDPOINT, params=params)
    if response.ok: return response.text

def datetime_from_position(start, position, resolution):
    if resolution == 'PT60M':
        return start.replace(hours=+position)
    raise NotImplementedError('Could not recognise resolution %s' % resolution)

def parse(xml_text):
    if not xml_text: return None
    soup = BeautifulSoup(xml_text, 'html.parser')
    resolution = soup.find_all('resolution')[0].contents[0]
    datetime_start = arrow.get(soup.find_all('start')[0].contents[0])
    last_entry = soup.find_all('point')[-1]
    quantity = float(last_entry.find_all('quantity')[0].contents[0])
    position = int(last_entry.find_all('position')[0].contents[0])
    datetime = datetime_from_position(datetime_start, position, resolution)
    return quantity, datetime

def get_biomass(values):
    if 'Biomass' in values or 'Fossil Peat' in values or 'Waste' in values:
        return values.get('Biomass', 0) + \
            values.get('Fossil Peat', 0) + \
            values.get('Waste', 0)

def get_coal(values):
    if 'Fossil Brown coal/Lignite' in values or 'Fossil Hard coal' in values:
        return values.get('Fossil Brown coal/Lignite', 0) + \
            values.get('Fossil Hard coal', 0)

def get_gas(values):
    if 'Fossil Coal-derived gas' in values or 'Fossil Gas' in values:
        return values.get('Fossil Coal-derived gas', 0) + \
            values.get('Fossil Gas', 0)

def get_hydro(values):
    if 'Hydro Pumped Storage' in values \
        or 'Hydro Run-of-river and poundage' in values \
        or 'Hydro Water Reservoir' in values:
        return max(values.get('Hydro Pumped Storage', 0), 0) + \
            values.get('Hydro Run-of-river and poundage', 0) + \
            values.get('Hydro Water Reservoir', 0)

def get_oil(values):
    if 'Fossil Oil' in values or 'Fossil Oil shale' in values:
        return values.get('Fossil Oil', 0) + values.get('Fossil Oil shale', 0)

def get_wind(values):
    if 'Wind Onshore' in values or 'Wind Offshore' in values:
        return values.get('Wind Onshore', 0) + values.get('Wind Offshore', 0)

def get_unknown(values):
    if 'Geothermal' in values \
        or 'Marine' in values \
        or 'Other renewable' in values \
        or 'Other' in values:
        return values.get('Geothermal', 0) + \
            values.get('Marine', 0) + \
            values.get('Other renewable', 0) + \
            values.get('Other', 0)

def fetch_PL():
    output_pairs = {}
    for k in ENTSOE_PARAMETER_DESC.keys():
        parsed = parse(query(k))
        if parsed: output_pairs[k] = parsed
    dates = set(map(lambda x: x[1], output_pairs.values()))
    if not len(dates) == 1:
        raise Exception('Measurements have been taken at different times: %s' % dates)

    values = {ENTSOE_PARAMETER_DESC[k]: v[0] for k, v in output_pairs.iteritems()}

    data = {
        'countryCode': COUNTRY_CODE,
        'production': {
            'biomass': values.get('Biomass', None),
            'coal': get_coal(values),
            'gas': get_gas(values),
            'hydro': get_hydro(values),
            'nuclear': values.get('Nuclear', None),
            'oil': get_oil(values),
            'solar': values.get('Solar', None),
            'wind': get_wind(values),
            'unknown': get_unknown(values)
        }
    }

    # Sanity check
    for k, v in data['production'].iteritems():
        if v is None: continue
        if v < 0: raise ValueError('key %s has negative value %s' % (k, v))

    return data

if __name__ == '__main__':
    print(fetch_PL())
