import arrow
import dateutil
import requests

COUNTRY_CODE = 'RO'

def fetch_RO():
    url = 'http://www.transelectrica.ro/sen-filter'
    data = requests.get(url).json()

    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(data['row1_HARTASEN_DATA'], "YY/M/D HH:mm:ss").replace(
            tzinfo=dateutil.tz.gettz('Europe/Bucharest'))
    }
    obj['consumption'] = {
        'unknown': float(data['CONS'])
    }
    # According to http://www.transelectrica.ro/widget/web/tel/sen-harta/-/harta_WAR_SENOperareHartaportlet
    # BALT and UCRS (for Baltic and Ukraine South) are categorized under Bulgary on transelectrica website. We did the same here.
    obj['exchange'] = {
        'BG': float(data['VARN']) + float(data['DOBR']) + float(data['KOZL1']) + float(data['KOZL2']) + float(data['BALT']) + float(data['UCRS'])
        'HU': float(data['SAND']) + float(data['BEKE1']) + float(data['BEKE2'])
        'MD': float(data['COSE']) + float(data['UNGE']) + float(data['CIOA']) + float(data['GOTE'])
        'RS': float(data['DJER']) + float(data['PAN1']) + float(data['PAN2']) + float(data['KUSJ']) + float(data['SIP_']) + float(data['KIKI'])
        'UA': float(data['VULC']) + float(data['MUKA']) + float(data['COD1'])
    }
    obj['production'] = {
        'biomass': float(data['BMASA']),
        'coal': float(data['CARB']),
        'gas': float(data['GAZE']),
        'hydro': float(data['APE']),
        'nuclear': float(data['NUCL']),
        'solar': float(data['FOTO']),
        'wind': float(data['EOLINA']),
    }

    return obj

if __name__ == '__main__':
    print fetch_RO()
