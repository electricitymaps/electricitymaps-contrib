#!/usr/bin/env python3

"""Parser for the Orkney Islands"""

import arrow
import dateutil
import dateutil.parser as dt_parser
import logging
import requests
from typing import Dict, Any

# data from https://www.ssen.co.uk/anm/orkney/


TZ = "Europe/London"
BASE_URL = "https://www.ssen.co.uk/Sse_Components/Views/Controls/FormControls/Handlers/ActiveNetworkManagementHandler.ashx?action=graph&contentId="

URL_ZONE_MAPPING = {
    "GB-ORK": BASE_URL + "14973",
}

GENERATION_MAPPING = {
    "Live Demand": "Demand",
    " ANM": "ANM Renewables",
    "Non-ANM Renewable Generation": "Non-ANM Renewables",
}


def parse_ssen_data(raw_data: Dict[str, Any], mapping: Dict) -> Dict:
    """Extracts only the data matching the mapping keys."""
    data = {}

    for item in raw_data["data"]["datasets"]:
        for ssen_label, map_label in mapping.items():
            if ssen_label in item["label"]: # string match
                data[map_label] = float(max(item["data"]))

    return data


def fetch_production(zone_key='GB-ORK', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given country
        Arguments:
        zone_key (optional) -- used in case a parser is able to fetch multiple countries
        session (optional)  -- request session passed in order to re-use an existing session
        Return:
        A dictionary in the form:
        {
          'zoneKey': 'FR',
          'datetime': '2017-01-01T00:00:00Z',
          'production': {
              'biomass': 0.0,
              'coal': 0.0,
              'gas': 0.0,
              'hydro': 0.0,
              'nuclear': null,
              'oil': 0.0,
              'solar': 0.0,
              'wind': 0.0,
              'geothermal': 0.0,
              'unknown': 0.0
          },
          'storage': {
              'hydro': -10.0,
          },
          'source': 'mysource.com'
        }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    s = session or requests.Session()
    response = s.get(URL_ZONE_MAPPING[zone_key], verify=False)

    response_dt = dt_parser.parse(response.headers.get("date"))
    dt = arrow.get(response_dt, TZ).datetime

    data = parse_ssen_data(response.json(), GENERATION_MAPPING)
    production_total = \
        data.get("ANM Renewables", 0.0) + data.get("Non-ANM Renewables", 0.0)

    data = {
        'zoneKey': zone_key,
        'datetime': dt,
        'production': {
            "unknown": production_total,
        },
        'storage': {
            'battery': None,
        },
        'source': 'ssen.co.uk'
    }

    return data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """Requests the last known power exchange (in MW) between two zones

    Arguments:
    zone_key1, zone_key2: specifies which exchange to get
    session (optional): request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. The provided target_datetime is timezone-aware in UTC.
    logger: an instance of a `logging.Logger`; all raised exceptions are also logged automatically

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'CA-QC->US-NEISO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))
    s = session or requests.Session()
    response = s.get(URL_ZONE_MAPPING[zone_key2], verify=False)

    response_dt = dt_parser.parse(response.headers.get("date"))
    dt = arrow.get(response_dt, TZ).datetime

    data = parse_ssen_data(response.json(), GENERATION_MAPPING)
    production_total = \
        data.get("ANM Renewables", 0.0) + data.get("Non-ANM Renewables", 0.0)
    # +ve importing from mainland, -ve export to mainland
    netflow = data.get("Demand") - production_total

    data = {'netFlow': netflow,
            'datetime': dt,
            'sortedZoneKeys': sorted_zone_keys,
            'source': 'ssen.co.uk'}

    return data


if __name__ == '__main__':
    from pprint import pprint as print

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(GB, GB-ORK)')
    print(fetch_exchange('GB', 'GB-ORK'))
