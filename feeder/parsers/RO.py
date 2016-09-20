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
    obj['exchange'] = {
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
