from bs4 import BeautifulSoup
import arrow, requests

COUNTRY_CODE = 'PL'
session = requests.session()

def fetchValue(params):

    now = arrow.utcnow()
    end = now.replace(hours=+2)
    start = now.replace(hours=-22)
    periodEnd = end.format('YYYYMMDDHH00')
    periodStart = start.format('YYYYMMDDHH00')

    parameters = '&psrType=' + params + '&documentType=A75&processType=A16&in_Domain=10YPL-AREA-----S&periodStart=' + periodStart + '&periodEnd=' + periodEnd
    url = 'https://transparency.entsoe.eu/api?securityToken=7466690c-c66a-4a00-8e21-2cb7d538f380' + parameters

    content = session.get(url)
    soup = BeautifulSoup(content.text, "html.parser")

    last = soup.find_all('point')[-1].find_all('quantity')[-1]
    value = str(last).strip("<quantity></quantity>")

    return float(value)

def fetch_PL():

    parameters = ["B01", "B02", "B03", "B04", "B05", "B06", "B10", "B11", "B12", "B19"]
    output_array = map(fetchValue, parameters)

    data = {
        'countryCode': COUNTRY_CODE,
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
