#!/usr/bin/env python3

# The arrow library is used to handle datetimes consistently with other parsers
import arrow

# The request library is used to fetch content through HTTP
import requests


timezone = 'Canada/Atlantic'


def _get_pei_info(requests_obj):
    url = 'http://www.gov.pe.ca/energy/js/chart-values.php'
    response = requests_obj.get(url)

    raw_data = response.json()[0]

    # meaning of keys per https://ruk.ca/content/open-data-pei-electricity
    data = {
        'pei_load': raw_data['data1'],
        'pei_wind_gen': raw_data['data2'],
        'pei_fossil_gen': raw_data['data3'],  # "Fossil Fueled Generation"
        'pei_wind_used': raw_data['data4'],
        'pei_wind_exported': raw_data['data5'],
        'utc_datetime': arrow.get(raw_data['updateDate']).datetime
    }

    return data


def fetch_production(zone_key='CA-PE', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key       -- ignored here, only information for CA-PE is returned
    session (optional) -- request session passed in order to re-use an existing session

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

    requests_obj = session or requests.session()
    raw_info = _get_pei_info(requests_obj)

    data = {
        'datetime': raw_info['utc_datetime'],
        'zoneKey': zone_key,
        'production': {
            'wind': raw_info['pei_wind_gen'],

            # These are oil-fueled ("heavy fuel oil" and "diesel") generators
            # used as peakers and back-up
            'oil': raw_info['pei_fossil_gen'],

            # specify some sources that definitely aren't present on PEI as zero,
            # this allows the analyzer to better estimate CO2eq
            'coal': 0,
            'hydro': 0,
            'nuclear': 0,
            'geothermal': 0
        },
        'storage': {},
        'source': 'www.gov.pe.ca/windenergy'
    }

    return data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two regions

    Arguments:
    zone_key1           -- the first country code (use format like "CA-QC" for sub-country regions)
    zone_key2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys != 'CA-NB->CA-PE':
        raise NotImplementedError('This exchange pair is not implemented')

    requests_obj = session or requests.session()
    raw_data = _get_pei_info(requests_obj)

    # PEI imports most of its electricity. Everything not generated on island
    # is imported from New Brunswick.
    # In case of wind, some is paper-"exported" even if there is a net import,
    # and 'pei_wind_used'/'data5' indicates their accounting of part of the load
    # served by non-exported wind.
    # # http://www.gov.pe.ca/windenergy/chart.php says:
    # "Wind Power Exported Off-Island is that portion of wind generation that is supplying
    # contracts elsewhere. The actual electricity from this portion of wind generation
    # may stay within PEI but is satisfying a contractual arrangement in another jurisdiction."
    # We are ignoring these paper exports, as they are an accounting/legal detail
    # that doesn't actually reflect what happens on the wires.
    # (New Brunswick being the only interconnection with PEI, "exporting" wind power to NB
    # then "importing" a balance of NB electricity likely doesn't actually happen.)
    imported_from_nb = (raw_data['pei_load'] - raw_data['pei_fossil_gen'] - raw_data['pei_wind_gen'])

    # In expected result, "net" represents an export.
    # We have sorted_zone_keys 'CA-NB->CA-PE', so it's export *from* NB,
    # and import *to* PEI.
    data = {
        'datetime': raw_data['utc_datetime'],
        'sortedZoneKeys': sorted_zone_keys,
        'netFlow': imported_from_nb,
        'source': 'www.gov.pe.ca/windenergy'
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())

    print('fetch_exchange("CA-PE", "CA-NB") ->')
    print(fetch_exchange("CA-PE", "CA-NB"))
