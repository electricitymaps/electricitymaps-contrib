# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import BalearicIslands
from parsers.lib.exceptions import ParserException


def fetch_consumption(country_code='ES-IB', session=None):
    ses = session or Session()
    responses = BalearicIslands(ses).get_all()
    if not responses:
        raise ParserException("ES-IB", "No response")
    else:
        data = []

        for response in responses:
            response_data = {
                'countryCode': country_code,
                'datetime': get(response.timestamp).datetime,
                'consumption': response.demand,
                'source': 'demanda.ree.es'
            }

            data.append(response_data)

        return data


def fetch_production(country_code='ES-IB', session=None):

    ses = session or Session()
    responses = BalearicIslands(ses).get_all()

    if not responses:
        raise ParserException("ES-IB", "No response")
    else:

        data = []

        for response in responses:
            response_data = {
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
                    'hydro': 0.0
                },
                'source': 'demanda.ree.es',
            }

            data.append(response_data)

        return data


def fetch_exchange(country_code1='ES', country_code2='ES-IB', session=None):

    ses = session or Session()
    responses = BalearicIslands(ses).get_all()
    if not responses:
        raise ParserException("ES-IB", "No response")
    else:

        data = []
        for response in responses:

            sorted_country_codes = sorted([country_code1, country_code2])
            net_flow = response.link['pe_ma']

            response_data = {
                'sortedCountryCodes': '->'.join(sorted_country_codes),
                'datetime': get(response.timestamp).datetime,
                'netFlow': net_flow if country_code1 == sorted_country_codes[0] else -1 * net_flow,
                'source': 'demanda.ree.es',
            }

            data.append(response_data)

        return data


if __name__ == '__main__':
    session = Session
    print fetch_consumption('ES-IB', session)
    print fetch_production('ES-IB', session)
    print fetch_exchange('ES', 'ES-IB', session)
