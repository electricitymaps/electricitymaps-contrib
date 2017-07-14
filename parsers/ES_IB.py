# The arrow library is used to handle datetimes
from arrow import get, utcnow
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import BalearicIslands


def fetch_consumption(country_code='ES-IB', session=None):
    ses = session or session()
    response = BalearicIslands(ses).get()

    if not response:
        return None
    else:
        data = {
            'countryCode': country_code,
            'datetime': get(response.timestamp).datetime,
            'consumption': response.demand,
            'source': 'demanda.ree.es'
        }

        return data


def fetch_production(country_code='ES-IB', session=None):

    ses = session or session()
    response = BalearicIslands(ses).get()

    if not response:
        return None
    else:
        datetime = get(response.timestamp).datetime
        data = {
            'countryCode': country_code,
            'datetime': datetime,
            'production': {
                'coal': response.carbon,
                'gas': round(response.gas + response.combined, 2),
                'solar': response.solar,
                'oil': round(response.vapor + response.diesel, 2),
                'wind': response.wind,
                'biomass': 0.0,
                'nuclear': 0.0,
                'geothermal': 0.0,
                'unknown': response.unknown()
            },
            'storage': {},
            'source': 'demanda.ree.es',
        }

        hidro = response.hydraulic
        if hidro >= 0.0:
            data['production']['hydro'] = hidro
            data['storage']['hydro'] = 0.0
        else:
            data['production']['hydro'] = 0.0
            data['storage']['hydro'] = abs(hidro)

        return data


def fetch_exchange(country_code1='ES', country_code2='ES-IB', session=None):

    ses = session or session()
    response = BalearicIslands(ses).get()
    if not response:
        return None
    else:
        sorted_country_codes = sorted([country_code1, country_code2])
        netFlow = response.link['pe_ma']

        data = {
            'sortedCountryCodes': '->'.join(sorted_country_codes),
            'datetime': get(response.timestamp).datetime,
            'netFlow': netFlow if country_code1 == sorted_country_codes[0] else -1 * netFlow,
            'source': 'demanda.ree.es',
        }

        return data


if __name__ == '__main__':
    session = Session
    print fetch_consumption('ES-IB', session)
    print fetch_production('ES-IB', session)
    print fetch_exchange('ES', 'ES-IB', session)
