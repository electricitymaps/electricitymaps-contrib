
from bs4 import BeautifulSoup
import urllib.request
import arrow

def fetchValue(params):

    now = arrow.utcnow()
    end = now.replace(hours=+2)
    start = now.replace(hours=-22)
    periodEnd = str(end.format('YYYYMMDDHH00'))
    periodStart = str(start.format('YYYYMMDDHH00'))

    parameters = '&psrType=' + params + '&documentType=A75&processType=A16&in_Domain=10YPL-AREA-----S&periodStart=' + periodStart + '&periodEnd=' + periodEnd
    link = 'https://transparency.entsoe.eu/api?securityToken=7466690c-c66a-4a00-8e21-2cb7d538f380' + parameters

    content = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(content, "lxml")

    quantity = []

    item = soup.find_all('point')
    for pos in item:
        p = pos.find_all('quantity')
        for x in p:
            quantity.append(x)

    last = quantity[len(quantity) - 1]
    value = str(last).strip("<quantity></quantity>")

    return float(value)


def fetchCountry():

    parameters = ["B01", "B02", "B03", "B04", "B05", "B06", "B10", "B11", "B12", "B19"]

    output_array = []
    for place in parameters:
        output_array.append(fetchValue(place))

    data = {
        'countryCode': "PL",
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
    print(fetchCountry())





