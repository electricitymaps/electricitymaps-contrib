#!/usr/bin/env python3

import datetime
import logging
import arrow
import requests
from bs4 import BeautifulSoup

try:
    unicode  # Python 2
except NameError:
    unicode = str  # Python 3

# This parser gets hourly electricity generation data from portalweb.cammesa.com/Memnet1/default.aspx
# for Argentina.  Currently wind and solar power are small contributors and not monitored but this is
# likely to change in the future.

# Useful links.
# https://en.wikipedia.org/wiki/Electricity_sector_in_Argentina
# https://en.wikipedia.org/wiki/List_of_power_stations_in_Argentina
# http://globalenergyobservatory.org/countryid/10#
# http://www.industcards.com/st-other-argentina.htm

#API Documentation: https://api.cammesa.com/demanda-svc/swagger-ui.html
CAMMESA_DEMANDA_ENDPOINT = 'https://api.cammesa.com/demanda-svc/generacion/ObtieneGeneracioEnergiaPorRegion/'
CAMMESA_RENEWABLES_ENDPOINT = 'https://cdsrenovables.cammesa.com/exhisto/RenovablesService/GetChartTotalTRDataSource/'

def fetch_production(zone_key='AR', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)) -> dict:
    """Requests the last known production mix (in MW) of a given country."""

    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    current_session = session or requests.session()
    country_details = {
            'zoneKey': zone_key,
            'production': {},
            'capacity': {},
            'storage': {},
            'source': 'api.cammesa.com',
        }

    non_renewables_mix, date = non_renewable_production_mix(zone_key, current_session)
    renewables_mix = renewables_production_mix(zone_key, current_session)
    country_details['production'] = full_production_mix(non_renewables_mix, renewables_mix)
    country_details['datetime'] = date

    return country_details

def full_production_mix(non_renewables_mix: dict, renewables_mix: dict):
    """Merges production mix data from different sources. Hydro comes from 
    different sources so they are added up."""

    production_mix = {'biomass': renewables_mix['biomass'],
                      'solar': renewables_mix['solar'],
                      'wind': renewables_mix['wind'],
                      'hydro': non_renewables_mix['hydro'] + renewables_mix['hydro'], 
                      'nuclear': non_renewables_mix['nuclear'],
                      'unknown': non_renewables_mix['unknown']}

    return production_mix

def renewables_production_mix(zone_key: str, session):
    """Retrieves production mix for renewables using CAMMESA's API"""

    today = datetime.datetime.strftime(datetime.date.today(),"%d-%m-%Y")
    params = {'desde': today, 'hasta': today}
    renewables_response = session.get(CAMMESA_RENEWABLES_ENDPOINT, params=params)
    assert renewables_response.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={} with payload={}'.format(
                                       zone_key, CAMMESA_RENEWABLES_ENDPOINT, params)

    production_info = renewables_response.json()
    sorted_production_info = sorted(production_info, key=lambda d: d['momento'])
    last_production_info = sorted_production_info[-1]

    production_mix = {'biomass': last_production_info['biocombustible'],
                        'hydro': last_production_info['hidraulica'],
                        'solar': last_production_info['fotovoltaica'],
                        'wind': last_production_info['eolica']}
    
    return production_mix

def non_renewable_production_mix(zone_key: str, session):
    """Retrieves production mix for non renewables using CAMMESA's API"""

    params = {'id_region': 1002}
    api_cammesa_response = session.get(CAMMESA_DEMANDA_ENDPOINT, params=params)
    assert api_cammesa_response.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={} with payload={}'.format(
                                       zone_key, CAMMESA_DEMANDA_ENDPOINT, params)

    production_info = api_cammesa_response.json()
    sorted_production_info = sorted(production_info, key=lambda d: d['fecha'])
    last_production_info = sorted_production_info[-1]

    production_mix = {'hydro': last_production_info['hidraulico'], 
                    'nuclear': last_production_info['nuclear'],
                    # As of 2022 thermal energy is mostly natural gas but 
                    # the data is not split. We put it into unknown for now.
                    # More info: see page 21 in https://microfe.cammesa.com/static-content/CammesaWeb/download-manager-files/Sintesis%20Mensual/Informe%20Mensual_2021-12.pdf
                    'unknown': last_production_info['termico']}

    # Parse the datetime and return a python datetime object in UTC
    date = arrow.get(last_production_info['fecha']).to('UTC').datetime
    
    return production_mix, date

def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""

    raise NotImplementedError('This exchange is not currently implemented')

def fetch_price(zone_key='AR', session=None, target_datetime=None,
                logger=logging.getLogger(__name__)) -> dict:
    """Requests the last known power price of a given country."""

    raise NotImplementedError('Fetching the price is not currently implemented')

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_exchange(AR, PY) ->')
    print(fetch_exchange('AR', 'PY'))
    print('fetch_exchange(AR, UY) ->')
    print(fetch_exchange('AR', 'UY'))
    print('fetch_exchange(AR, CL-SEN) ->')
    print(fetch_exchange('AR', 'CL-SEN'))
