#!/usr/bin/env python3
# coding=utf-8

"""Parser for Moldova."""

import arrow
import requests


display_url = 'http://www.moldelectrica.md/ro/activity/system_state'
data_url = 'http://www.moldelectrica.md/utils/load5.php'

# To match the fields with the respective index and meaning,
# I used the following code which may be used in the future for maintenance:
# https://gist.github.com/Impelon/09407f739cdff05134f8c77cb7a92ada

# Fields that can be fetched from data_url linked to production.
# Types of production and translations have been added manually.
production_fields = (
    {'index': 2, 'name': 'NHE Costeşti', 'type': 'hydro'},  # run-of-river
    {'index': 3, 'name': 'CET Nord', 'type': 'gas'},  # CHPP
    {'index': 4, 'name': 'NHE Dubăsari', 'type': 'hydro'},
    {'index': 5, 'name': 'CET-2 Chişinău', 'type': 'gas'},  # CHPP
    {'index': 6, 'name': 'CET-1 Chişinău', 'type': 'gas'},  # CHPP
    {'index': 7, 'name': 'CERS Moldovenească', 'type': 'gas'},  # fuel mix: 99.94% gas, 0.01% coal, 0.05% oil (2020)
)
# Other relevant fields that can be fetched from data_url.
other_fields = (
    {'index': 26, 'name': 'consumption'},
    {'index': 27, 'name': 'generation'},
    {'index': 28, 'name': 'exchange UA->MD'},
    {'index': 29, 'name': 'exchange RO->MD'},
    {'index': 30, 'name': 'utility frequency'},
)

# Further information on the equipment used at CERS Moldovenească can be found at:
# http://moldgres.com/o-predpriyatii/equipment
# Further information on the fuel-mix used at CERS Moldovenească can be found at:
# http://moldgres.com/search/%D0%9F%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B5%20%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B8
# (by searching for 'Производственные показатели' aka. 'Performance Indicators')
# Data for the fuel-mix at CERS Moldovenească for the year 2020 can be found at:
# http://moldgres.com/wp-content/uploads/2021/02/proizvodstvennye-pokazateli-zao-moldavskaja-gres-za-2020-god.pdf

# Annual reports from moldelectrica can be found at:
# https://moldelectrica.md/ro/network/annual_report


def get_data(session=None) -> list:
    """Returns data as a list of floats."""
    s = session or requests.Session()

    # In order for data_url to return data, cookies from display_url must be obtained then reused.
    response = s.get(display_url, verify=False)
    data_response = s.get(data_url, verify=False)
    raw_data = data_response.text
    try:
        data = [float(i) if i else None for i in raw_data.split(',')]
    except:
        raise Exception('Not able to parse received data. Check that the specifed URL returns correct data.')

    return data


def fetch_production(zone_key='MD', session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    field_values = get_data(session)
    production = {'solar': None, 'wind': None, 'biomass': 0.0, 'nuclear': 0.0, 'gas': 0.0, 'hydro': 0.0}

    non_renewables_production = 0.0
    for field in production_fields:
        produced = field_values[field['index']]
        non_renewables_production += produced
        production[field['type']] += produced

    # Renewables (solar + biogas + wind) make up a small part of the energy produced.
    # They do not have an explicit entry,
    # hence the difference between the actual generation and
    # the sum of all other sectors are the renewables.
    # The exact mix of renewable enegry sources is unknown,
    # so everything is attributed to biomass.
    production['biomass'] = field_values[other_fields[1]['index']] - non_renewables_production

    consumption = field_values[other_fields[0]['index']]

    dt = arrow.now('Europe/Chisinau').datetime

    datapoint = {
        'zoneKey': zone_key,
        'datetime': dt,
        'consumption': consumption,
        'production': production,
        'storage': {},
        'source': 'moldelectrica.md'
    }

    return datapoint


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))

    field_values = get_data(session)

    if sortedZoneKeys == 'MD->UA':
        netflow = -1 * field_values[other_fields[2]['index']]
    elif sortedZoneKeys == 'MD->RO':
        netflow = -1 * field_values[other_fields[3]['index']]
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    dt = arrow.now('Europe/Chisinau').datetime

    exchange = {
        'sortedZoneKeys': sortedZoneKeys,
        'datetime': dt,
        'netFlow': netflow,
        'source': 'moldelectrica.md'
    }

    return exchange


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(MD, UA) ->')
    print(fetch_exchange('MD', 'UA'))
    print('fetch_exchange(MD, RO) ->')
    print(fetch_exchange('MD', 'RO'))
