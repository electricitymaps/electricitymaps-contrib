import arrow
import requests

def fetch_production(country_code='EE', session=None):
    url = 'http://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview'

    data = (session or requests).get(url).json()
    countries = map(lambda x: x['value'], data['Headers'])
    i = countries.index(country_code)

    obj = {
        'countryCode': country_code,
        'datetime': arrow.get(data['MeasuredAt'] / 1000).datetime, # time given in UTC
        'source': 'statnett.no'
    }
    obj['consumption'] = {
        'unknown': float(data['ConsumptionData'][i]['value'].replace(u'\xa0', '').replace(' ', '').replace('-', '0'))
    }
    obj['production'] = {
        'unknown': float(data['ThermalData'][i]['value'].replace(u'\xa0', '').replace(' ', '').replace('-', '0')) + 
            float(data['NotSpecifiedData'][i]['value'].replace(u'\xa0', '').replace(' ', '').replace('-', '0')),
        'wind': float(data['WindData'][i]['value'].replace(u'\xa0', '').replace(' ', '').replace('-', '0')),
        'nuclear': float(data['NuclearData'][i]['value'].replace(u'\xa0', '').replace(' ', '').replace('-', '0')),
        'hydro': float(data['HydroData'][i]['value'].replace(u'\xa0', '').replace(' ', '').replace('-', '0')),
    }

    return obj

if __name__ == '__main__':
    print fetch_production()
