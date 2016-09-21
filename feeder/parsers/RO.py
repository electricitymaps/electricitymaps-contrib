import arrow
import dateutil
import requests

COUNTRY_CODE = 'RO'

def fetch_RO():
    url = 'http://www.transelectrica.ro/sen-filter'
    data = {}
    for item in requests.get(url).json():
        d = list(item.iteritems())[0]
        data[d[0]] = d[1]
    
    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(data['row1_HARTASEN_DATA'], "YY/M/D H:mm:ss").replace(
            tzinfo=dateutil.tz.gettz('Europe/Bucharest')).datetime
    }
    obj['consumption'] = {
        'unknown': float(data['CONS'])
    }
    # According to http://www.transelectrica.ro/widget/web/tel/sen-harta/-/harta_WAR_SENOperareHartaportlet
    # BALT and UCRS (for Baltic and Ukraine South) are categorized under Bulgary on transelectrica website. We did the same here.
    obj['exchange'] = {
        'BG': float(data.get('VARN', 0)) + float(data.get('DOBR', 0)) + float(data.get('KOZL1', 0)) + float(data.get('KOZL2', 0)) + float(data.get('BALT', 0)) + float(data.get('UCRS', 0)),
        'HU': float(data.get('SAND', 0)) + float(data.get('BEKE1', 0)) + float(data.get('BEKE2', 0)),
        'MD': float(data.get('COSE', 0)) + float(data.get('UNGE', 0)) + float(data.get('CIOA', 0)) + float(data.get('GOTE', 0)),
        'RS': float(data.get('DJER', 0)) + float(data.get('PAN1', 0)) + float(data.get('PAN2', 0)) + float(data.get('KUSJ', 0)) + float(data.get('SIP_', 0)) + float(data.get('KIKI', 0)),
        'UA': float(data.get('VULC', 0)) + float(data.get('MUKA', 0)) + float(data.get('COD1', 0))
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

    return obj

if __name__ == '__main__':
    print fetch_RO()
