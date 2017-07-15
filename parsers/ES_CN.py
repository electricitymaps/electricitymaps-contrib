# The arrow library is used to handle datetimes
from arrow import get, utcnow
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import CanaryIslands, NoDataException, TimestampException


def fetch_consumption(country_code='ES-CN', session=None):
    ses = session or session()

    try:
        response = CanaryIslands(ses).get()
    except NoDataException:
        return None
    except TimestampException:
        return None

    data = {
        'countryCode': country_code,
        'datetime': get(response.timestamp).datetime,
        'consumption': response.demand,
        'source': 'demanda.ree.es'
    }

    return data


def fetch_production(country_code='ES-CN', session=None):
    ses = session or session()

    try:
        response = CanaryIslands(ses).get()
    except NoDataException:
        return None
    except TimestampException:
        return None

    data = {
        'countryCode': country_code,
        'datetime': get(response.timestamp).datetime,
        'production': {
            'coal': response.carbon,
            'gas': round(response.gas + response.combined, 2),
            'solar': response.solar,
            'oil': round(response.vapor + response.diesel, 2),
            'wind': response.wind,
            'hydro': response.hydraulic,
            'biomass': 0.0,
            'nuclear': 0.0,
            'geothermal': 0.0,
            'unknown': response.unknown()
        },
        'storage': {
            'hydro': response.storage
        },
        'source': 'demanda.ree.es',
    }

    return data


if __name__ == '__main__':
    session = Session
    print fetch_consumption('ES-CN', session)
    print fetch_production('ES-CN', session)
