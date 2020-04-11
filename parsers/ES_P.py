import logging

# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from ree import (IberianPeninsula)
from .lib.exceptions import ParserException
from parsers.lib.validation import validate

# how do i find floor
floor = 0


def fetch_consumption(zone_key='ES_P', session=None, target_datetime=None, logger=None):
    ses = session or Session()
    IberianPeninsula_data = IberianPeninsula(ses, verify=False).get()
    if not IberianPeninsula_data:
        raise ParserException(zone_key, "IberianPeninsula not response")
    response_data = {
        'zoneKey': zone_key,
        'datetime': get(IberianPeninsula_data.timestamp).datetime,
        'consumption': IberianPeninsula_data.demand,
        'source': 'demanda.ree.es'
    }

    return response_data


def fetch_production(zone_key, session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    ses = session or Session()
    response = IberianPeninsula(ses, verify=False).get()
    if not response:
        raise ParserException(zone_key, "IberianPeninsula not response")
    if response.production() > 0:
        response_data = {
            'zoneKey': zone_key,
            'datetime': get(response.timestamp).datetime,
            'production': {
                'coal': response.carbon,
                'gas': round(response.gas + response.combined, 2),
                'solar': response.solar,
                # oil is found differently in ES_IB and ES_CN
                'oil': round(response.vapor + response.diesel, 2),
                'wind': response.wind,
                'hydro': response.hydraulic,
                'biomass': response.waste,
                # not sure about biomass either
                'nuclear': response.nuclear,
                'geothermal': 0.0,
                'unknown': response.other
            },
            'storage': {
                'hydro': 0.0,
                'battery': 0.0
            },
            'source': 'demanda.ree.es',
        }
        response_data = validate(response_data, logger,
                             floor=floor)
        return response_data


if __name__ == '__main__':
    session = Session
    print("# ES-IberianPeninsula")
    print(fetch_consumption('ES_P', session))
    print(fetch_production('ES_P', session))
