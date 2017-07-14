# The arrow library is used to handle datetimes
from arrow import get, utcnow
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import BalearicIslands, NoDataException, TimestampException


def fetch_consumption(country_code='ES-IB', session=None):
    ses = session or session()
    try:
        response = BalearicIslands(ses).get()
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


def fetch_production(country_code='ES-IB', session=None):

    ses = session or session()
    response = BalearicIslands(ses).get()

    if not response:
        datetime = utcnow().datetime
    else:
        datetime = get(response.timestamp).datetime

    data = {
        'countryCode': country_code,
        'datetime': datetime,
        'production': {
          'biomass': 0.0,
          'nuclear': 0.0,
          'geothermal': 0.0
        },
        'storage': {},
        'source': 'demanda.ree.es',
    }

    if response:
        data['production']['coal'] = response.carbon
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


def fetch_exchange(country_code1='ES', country_code2='ES-IB', session=None):

    ses = session or session()
    response = BalearicIslands(ses).get()
    if not response:
        datetime = utcnow().datetime
    else:
        datetime = get(response.timestamp).datetime

    sorted_country_codes = sorted([country_code1, country_code2])

    data = {
        'sortedCountryCodes': '->'.join(sorted_country_codes),
        'datetime': datetime,
        'source': 'demanda.ree.es',
    }

    if response:
        netFlow = response.link['pe_ma']
        data['netFlow'] = netFlow if country_code1 == sorted_country_codes[0] else -1 * netFlow

    return data


if __name__ == '__main__':
    session = Session
    print fetch_consumption('ES-IB', session)
    print fetch_production('ES-IB', session)
    print fetch_exchange('ES', 'ES-IB', session)
