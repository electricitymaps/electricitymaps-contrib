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

def query_production(psr_type, in_domain, session):
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
        return # Return by default
        # Grab the error if possible
        soup = BeautifulSoup(response.text, 'html.parser')
        print 'Failed for psr %s' % psr_type
        print 'Reason:', soup.find_all('text')[0].contents[0]

def query_exchange(in_domain, out_domain, session):
    now = arrow.utcnow()
    params = {
        'documentType': 'A11',
        'in_Domain': in_domain,
        'out_Domain': out_domain,
        'periodStart': now.replace(hours=-24).format('YYYYMMDDHH00'),
        'periodEnd': now.replace(hours=+24).format('YYYYMMDDHH00'),
        'securityToken': os.environ['ENTSOE_TOKEN']
    }
    response = session.get(ENTSOE_ENDPOINT, params=params)
    if response.ok: return response.text
    else:
        return # Return by default
        # Grab the error if possible
        soup = BeautifulSoup(response.text, 'html.parser')
        print 'Failed to get exchange. Reason:', soup.find_all('text')[0].contents[0]

def datetime_from_position(start, position, resolution):
    m = re.search('PT(\d+)([M])', resolution)
    if m:
        digits = int(m.group(1))
        scale = m.group(2)
        if scale == 'M':
            return start.replace(minutes=position * digits)
    raise NotImplementedError('Could not recognise resolution %s' % resolution)

def parse_production(xml_text):
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

def parse_exchange(xml_text, is_import, quantities=None, datetimes=None):
    if not xml_text: return None
    if not quantities: quantities = []
    if not datetimes: datetimes = []
    soup = BeautifulSoup(xml_text, 'html.parser')
    # Get all points
    for timeseries in soup.find_all('timeseries'):
        resolution = timeseries.find_all('resolution')[0].contents[0]
        datetime_start = arrow.get(timeseries.find_all('start')[0].contents[0])
        for entry in timeseries.find_all('point'):
            quantity = float(entry.find_all('quantity')[0].contents[0])
            if not is_import: quantity *= -1
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

def fetch_ENTSOE(in_domain, connecting_domains, country_code, session=None):
    if not session: session = requests.session()
    # Create a double hashmap with keys (datetime, parameter)
    production_hashmap = defaultdict(lambda: {})
    # Create a double hashmap with keys (datetime, country_code)
    exchange_hashmap = defaultdict(lambda: {})
    # Grab production
    for k in ENTSOE_PARAMETER_DESC.keys():
        parsed = parse_production(query_production(k, in_domain, session))
        if parsed:
            quantities, datetimes = parsed
            for i in range(len(quantities)):
                production_hashmap[datetimes[i]][k] = quantities[i]
    # Grab exchange
    for connecting_country_code, connecting_domain in connecting_domains.iteritems():
        # Import
        parsed = parse_exchange(
            query_exchange(in_domain, connecting_domain, session),
            is_import=True)
        if parsed:
            # Export
            parsed = parse_exchange(
                xml_text=query_exchange(connecting_domain, in_domain, session),
                is_import=False, quantities=parsed[0], datetimes=parsed[1])
            if parsed:
                quantities, datetimes = parsed
                for i in range(len(quantities)):
                    exchange_hashmap[datetimes[i]][connecting_country_code] = quantities[i]

    # Take the last production date that is present for all parameters
    production_dates = sorted(set(production_hashmap.keys()), reverse=True)
    if not len(production_dates): raise Exception('%s [%s]: No production data was returned' % (country_code, in_domain))
    production_dates_with_counts = map(lambda date: len(production_hashmap[date].keys()),
        production_dates)
    production_date = production_dates[production_dates_with_counts.index(max(production_dates_with_counts))]

    values = {ENTSOE_PARAMETER_DESC[k]: v for k, v in production_hashmap[production_date].iteritems()}

    data = {
        'countryCode': country_code,
        'datetime': production_date.datetime,
        'productionDatetime': production_date.datetime,
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

    # Find the closest matching exchange
    dates_exchange = sorted(set(exchange_hashmap.keys()), reverse=True)
    if len(dates_exchange):
        delta_hours = map(lambda i: abs((production_date - dates_exchange[i]).total_seconds()) / 3600.0,
            range(len(dates_exchange)))
        min_delta_hours = min(delta_hours)
        if min_delta_hours <= 1.0:
            exchange_date = dates_exchange[delta_hours.index(min_delta_hours)]
            data['exchangeDatetime'] = exchange_date.datetime
            data['exchange'] = exchange_hashmap[production_date]
        else: print 'Skipping exchange because time delta was %dh' % min_delta_hours

    # Sanity check
    for k, v in data['production'].iteritems():
        if v is None: continue
        if v < 0: raise ValueError('key %s has negative value %s' % (k, v))

    return data
