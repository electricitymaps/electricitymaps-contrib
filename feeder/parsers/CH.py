import arrow
import requests


COUNTRY_CODE = 'CH'

def fetch_CH(session=None):
    #gets powerflows from Swissgrid
    url = 'https://www.swissgrid.ch/mvc.do/getLiveData'
    data = requests.get(url).json()
    data = data['data']

    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(data[0]['_pbnValues'][0]['time']).datetime #time given in UTC
    }

    obj['exchange'] = {
        'DE': data[1]['_pbnValues'][0]['value1'],
        'AT': data[2]['_pbnValues'][0]['value1'],
        'FR': data[3]['_pbnValues'][0]['value1'],
        'IT': data[4]['_pbnValues'][0]['value1']
    }

    return obj

if __name__ == '__main__':
    print fetch_CH()