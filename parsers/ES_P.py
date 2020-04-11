import logging

# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from ree import (IberianPeninsula)
from .lib.exceptions import ParserException
from parsers.lib.validation import validate

FLOORS = {
    'ES-P': 0,
}


def fetch_consumption(zone_key='ES_P', session=None, target_datetime=None, logger=None):
    ses = session or Session()
    IberianPeninsula_data = IberianPeninsula(ses, verify=False).get()
    if not IberianPeninsula_data:
        raise ParserException(zone_key, "IberianPeninsula not response")
    data = []
    response_data = {
            'zoneKey': zone_key,
            'datetime': get(IberianPeninsula_data.timestamp).datetime,
            'consumption': IberianPeninsula_data.demand,
            'source': 'demanda.ree.es'
        }

    data.append(response_data)

    return data


if __name__ == '__main__':
    session = Session
    print("# ES-IberianPeninsula")
    print(fetch_consumption('ES_P', session))
