from bs4 import BeautifulSoup
from collections import defaultdict
import arrow, os, re, requests

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

def query(psr_type, in_domain, session):
    now = arrow.utcnow()
    params = {
        'psrType': psr_type,
        'documentType': 'A75',
        'processType': 'A16',
        'in_Domain': in_domain,
        'periodStart': now.replace(hours=-24).format('YYYYMMDDHH00'),
        'periodEnd': now.replace(hours=+24).format('YYYYMMDDHH00'),
        'securityToken': os.environ['ENTSOE_TOKEN']
    }
    response = session.get(ENTSOE_ENDPOINT, params=params)
    if response.ok: return response.text
    else: 
        # Grab the error if possible
        soup = BeautifulSoup(response.text, 'html.parser')
        print 'Failed for psr %s' % psr_type
        print 'Reason:', soup.find_all('text')[0].contents[0]

def datetime_from_position(start, position, resolution):
    m = re.search('PT(\d+)([M])', resolution)
    if m:
        digits = int(m.group(1))
        scale = m.group(2)
        if scale == 'M':
            return start.replace(minutes=position * digits)
    raise NotImplementedError('Could not recognise resolution %s' % resolution)

def parse(xml_text):
    if not xml_text: return None
    soup = BeautifulSoup(xml_text, 'html.parser')
    # Get all points
    quantities = []
    datetimes = []
    for timeseries in soup.find_all('timeseries'):
        resolution = timeseries.find_all('resolution')[0].contents[0]
        datetime_start = arrow.get(timeseries.find_all('start')[0].contents[0])
        is_production = len(timeseries.find_all('inBiddingZone_Domain.mRID'.lower())) > 0
        for entry in timeseries.find_all('point'):
            quantity = float(entry.find_all('quantity')[0].contents[0])
            # Is this is not a production, then it is storage (consumption)
            if not is_production: quantity *= -1
            position = int(entry.find_all('position')[0].contents[0])
            datetime = datetime_from_position(datetime_start, position, resolution)
            # Find out whether or not we should update the net production
            try:
                i = datetimes.index(datetime)
                quantities[i] += quantity
            except ValueError: # Not in list
                quantities.append(quantity)
                datetimes.append(datetime)
    return quantities, datetimes

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

def fetch_ENTSOE(in_domain, country_code, session=None):
    if not session: session = requests.session()
    # Create a double hashmap with keys (datetime, parameter)
    output_dated_pairs = defaultdict(lambda: {})
    for k in ENTSOE_PARAMETER_DESC.keys():
        parsed = parse(query(k, in_domain, session))
        if parsed:
            quantities, datetimes = parsed
            for i in range(len(quantities)):
                output_dated_pairs[datetimes[i]][k] = quantities[i]
    # Take the last date that is present for all parameters
    dates = sorted(set(output_dated_pairs.keys()), reverse=True)
    if not len(dates): raise Exception('Not data was returned')
    dates_with_counts = map(lambda date: len(output_dated_pairs[date].keys()),
        dates)
    date = dates[dates_with_counts.index(max(dates_with_counts))]

    values = {ENTSOE_PARAMETER_DESC[k]: v for k, v in output_dated_pairs[date].iteritems()}

    data = {
        'countryCode': country_code,
        'datetime': date.datetime,
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
