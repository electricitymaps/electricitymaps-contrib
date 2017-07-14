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
        response = None
    except TimestampException:
        response = None

    if not response:
        datetime = utcnow().datetime
    else:
        datetime = get(response.timestamp).datetime

    data = {
        'countryCode': country_code,
        'datetime': datetime,
        'source': 'demanda.ree.es'
    }

    if response:
        data['consumption'] = response.demand

    return data


def fetch_production(country_code='ES-CN', session=None):
    ses = session or session()

    try:
        response = CanaryIslands(ses).get()
    except NoDataException:
        response = None
    except TimestampException:
        response = None

    if not response:
        datetime = utcnow().datetime
    else:
        datetime = get(response.timestamp).datetime

    data = {
        'countryCode': country_code,
        'datetime': datetime,
        'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'nuclear': 0.0,
          'geothermal': 0.0
        },
        'storage': {},
        'source': 'demanda.ree.es',
    }

    if response:
        data['production']['gas'] = response.gas + response.combined
        data['production']['solar'] = response.solar
        data['production']['oil'] = response.vapor + response.diesel
        data['production']['wind'] = response.wind

        hidro = response.hydraulic
        if hidro >= 0.0:
            data['production']['hydro'] = hidro
            data['storage']['hydro'] = 0.0
        else:
            data['production']['hydro'] = 0.0
            data['storage']['hydro'] = abs(hidro)

        data['production']['unknown'] = response.unknown()

    return data


if __name__ == '__main__':
    session = Session
    print fetch_consumption('ES-CN', session)
    print fetch_production('ES-CN', session)
