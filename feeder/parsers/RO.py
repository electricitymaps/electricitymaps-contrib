import arrow
import dateutil
import requests

def fetch(session=None):
    url = 'http://www.transelectrica.ro/sen-filter'
    data = {}
    for item in (session or requests).get(url).json():
        d = list(item.iteritems())[0]
        data[d[0]] = d[1]
    return data

def fetch_production(country_code='RO', session=None):
    data = fetch(session)
    
    obj = {
        'countryCode': country_code,
        'datetime': arrow.get(data['row1_HARTASEN_DATA'], "YY/M/D H:mm:ss").replace(
            tzinfo=dateutil.tz.gettz('Europe/Bucharest')).datetime,
        'source': 'transelectrica.ro'
    }
    obj['consumption'] = {
        'unknown': float(data['CONS'])
    }
    obj['production'] = {
        'biomass': float(data['BMASA']),
        'coal': float(data['CARB']),
        'gas': float(data['GAZE']),
        'hydro': float(data['APE']),
        'nuclear': float(data['NUCL']),
        'solar': float(data['FOTO']),
        'wind': float(data['EOLIAN'])
    }
    if obj['production']['solar'] == -1.0: del obj['production']['solar']

    return obj

def fetch_exchange(country_code1, country_code2, session=None):
    if country_code1 == 'RO': 
        direction = 1
        target = country_code2
    elif country_code2 == 'RO': 
        direction = -1
        target = country_code1
    else: return None
    data = fetch(session)
    obj = {
        'sortedCountryCodes': '->'.join(sorted([country_code1, country_code2])),
        'datetime': arrow.get(data['row1_HARTASEN_DATA'], "YY/M/D H:mm:ss").replace(
            tzinfo=dateutil.tz.gettz('Europe/Bucharest')).datetime,
        'source': 'transelectrica.ro',
    }
    # According to http://www.transelectrica.ro/widget/web/tel/sen-harta/-/harta_WAR_SENOperareHartaportlet
    # BALT and UCRS (for Baltic and Ukraine South) are categorized under Bulgary on transelectrica website. We did the same here.
    if target == 'BG':
        obj['netFlow'] = direction * float(data.get('VARN', 0)) + float(data.get('DOBR', 0)) + float(data.get('KOZL1', 0)) + float(data.get('KOZL2', 0)) + float(data.get('BALT', 0)) + float(data.get('UCRS', 0))
    elif target == 'HU':
        obj['netFlow'] = direction * float(data.get('SAND', 0)) + float(data.get('BEKE1', 0)) + float(data.get('BEKE2', 0))
    elif target == 'MD':
        obj['netFlow'] = direction * float(data.get('COSE', 0)) + float(data.get('UNGE', 0)) + float(data.get('CIOA', 0)) + float(data.get('GOTE', 0))
    elif target == 'RS':
        obj['netFlow'] = direction * float(data.get('DJER', 0)) + float(data.get('PAN1', 0)) + float(data.get('PAN2', 0)) + float(data.get('KUSJ', 0)) + float(data.get('SIP_', 0)) + float(data.get('KIKI', 0))
    elif target == 'UA':
        obj['netFlow'] = direction * float(data.get('VULC', 0)) + float(data.get('MUKA', 0)) + float(data.get('COD1', 0))
    else: raise Exception('Unhandled case')
    return obj

if __name__ == '__main__':
    print fetch_production()
