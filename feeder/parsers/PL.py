from bs4 import BeautifulSoup
import arrow, os, requests

COUNTRY_CODE = 'PL'
date = arrow.now(tz='Europe/Warsaw').format('DD/MM/YYYY HH:mm:ss')
session = requests.session()
ENTSOE_TOKEN = os.environ.get('ENTSOE_TOKEN')

def fetchValue(params):

    now = arrow.utcnow()
    end = now.replace(hours=+24)
    start = now.replace(hours=-22)
    periodEnd = end.format('YYYYMMDDHH00')
    periodStart = start.format('YYYYMMDDHH00')

    parameters = '&psrType=' + params + '&documentType=A75&processType=A16&in_Domain=10YPL-AREA-----S&periodStart=' + periodStart + '&periodEnd=' + periodEnd
    url = 'https://transparency.entsoe.eu/api?securityToken=' + ENTSOE_TOKEN + parameters

    content = session.get(url)
    soup = BeautifulSoup(content.text, "html.parser")

    last = soup.find_all('point')[-1].find_all('quantity')[-1]
    value = last.contents[0]

    return float(value)

def fetch_PL():

    parameters = ["B01", "B02", "B03", "B04", "B05", "B06", "B10", "B11", "B12", "B19"]
    output_array = map(fetchValue, parameters)

    data = {
        'countryCode': COUNTRY_CODE,
        'datetime': date,
        'production': {
            'wind': output_array[9],
            'solar': 0,
            'hydro': output_array[6] + output_array[7] + output_array[8],
            'biomass': output_array[0],
            'nuclear': 0,
            'gas': output_array[2] + output_array[3],
            'coal': output_array[1] + output_array[4],
            'oil': output_array[5],
            'unknown': 0
        }
    }

    return data

if __name__ == '__main__':
    print(fetch_PL())
