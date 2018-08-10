#!/usr/bin/env python3

import arrow
import pandas
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

MX_EXCHANGE_URL = 'http://www.cenace.gob.mx/Paginas/Publicas/Info/DemandaRegional.aspx'

EXCHANGES = {"MX-NO->MX-NW": "IntercambioNTE-NOR",
             "MX-NE->MX-NO": "IntercambioNES-NTE",
             "MX-NE->MX-OR": "IntercambioNES-ORI",
             "MX-OR->MX-PN": "IntercambioORI-PEN",
             "MX-CE->MX-OR": "IntercambioORI-CEL",
             "MX-OC->MX-OR": "IntercambioOCC-ORI",
             "MX-CE->MX-OC": "IntercambioOCC-CEL",
             "MX-NE->MX-OC": "IntercambioNES-OCC",
             "MX-NO->MX-OC": "IntercambioNTE-OCC",
             "MX-NW->MX-OC": "IntercambioNOR-OCC",
             "MX-NO->US": "IntercambioUSA-NTE",
             "MX-NE->US": "IntercambioUSA-NES",
             "BZ->MX-PN": "IntercambioPEN-BEL"
             }


def fetch_MX_exchange(sorted_zone_keys, s):
    """
    Finds current flow between two Mexican control areas.
    Returns a float.
    """

    req = s.get(MX_EXCHANGE_URL)
    soup = BeautifulSoup(req.text, 'html.parser')
    exchange_div = soup.find("div", attrs={'id': EXCHANGES[sorted_zone_keys]})
    val = exchange_div.text

    # cenace html uses unicode hyphens instead of minus signs and , as thousand separator
    trantab = str.maketrans({chr(8208): chr(45), ",": ""})

    val = val.translate(trantab)
    flow = float(val)

    if sorted_zone_keys in ["BZ->MX-PN", "MX-CE->MX-OR", "MX-CE->MX-OC"]:
        # reversal needed for these zones due to EM ordering
        flow = -1*flow

    return flow


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger=None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    zone_key1: the first country code
    zone_key2: the second country code; order of the two codes in params
      doesn't matter
    session: request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """
    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys not in EXCHANGES:
        raise NotImplementedError('Exchange pair not supported: {}'.format(sorted_zone_keys))

    s = session or requests.Session()

    netflow = fetch_MX_exchange(sorted_zone_keys, s)

    data = {
      'sortedZoneKeys': sorted_zone_keys,
      'datetime': arrow.now('America/Tijuana').datetime,
      'netFlow': netflow,
      'source': 'cenace.gob.mx'
    }

    return data


if __name__ == '__main__':
    print("fetch_exchange(MX-NO, MX-NW)")
    print(fetch_exchange("MX-NO", "MX-NW"))
    print("fetch_exchange(MX-OR, MX-PN)")
    print(fetch_exchange("MX-OR", "MX-PN"))
    print("fetch_exchange(MX-NE, MX-OC)")
    print(fetch_exchange("MX-NE", "MX-OC"))
    print("fetch_exchange(MX-NE, MX-NO)")
    print(fetch_exchange("MX-NE", "MX-NO"))
    print("fetch_exchange(MX-OC, MX-OR)")
    print(fetch_exchange("MX-OC", "MX-OR"))
    print("fetch_exchange(MX-NE, US)")
    print(fetch_exchange("MX-NE", "US"))
    print("fetch_exchange(MX-CE, MX-OC)")
    print(fetch_exchange("MX-CE", "MX-OC"))
    print("fetch_exchange(MX-PN, BZ)")
    print(fetch_exchange("MX-PN", "BZ"))
    print("fetch_exchange(MX-NO, MX-OC)")
    print(fetch_exchange("MX-NO", "MX-OC"))
    print("fetch_exchange(MX-NO, US)")
    print(fetch_exchange("MX-NO", "US"))
    print("fetch_exchange(MX-NE, MX-OR)")
    print(fetch_exchange("MX-NE", "MX-OR"))
    print("fetch_exchange(MX-CE, MX-OR)")
    print(fetch_exchange("MX-CE", "MX-OR"))
