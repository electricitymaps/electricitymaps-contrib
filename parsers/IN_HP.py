#!/usr/bin/env python3

"""Parser for Himachal Pradesh (Indian State)."""

import arrow
import datetime
import logging
import requests
from bs4 import BeautifulSoup
from enum import Enum


DATA_URL = 'https://hpsldc.com/intra-state-power-transaction/'
ZONE_KEY = 'IN_HP'
TZ = 'Asia/Kolkata'


class GenType(Enum):
    """Enum for plant generation types found in the data.
    Enum values are the keys for the production/consumption
    dictionaries returned from fetch_production() and fetch_consumption()."""
    HYDRO = 'hydro'
    UNKNOWN = 'unknown'


# Map of plant names (as given in data source) to their type.
# Source for types is http://meritindia.in/state-data/himachal-pradesh
# or the link next to the relevant entry if there is no record in the above.
PLANT_NAMES_TO_TYPES = {
    # Plants in GENERATION OF HP(Z) table:
    'BASPA': GenType.HYDRO,  # Listed as ISGS in type source but state in data source
    'BHABA': GenType.HYDRO,
    'GIRI': GenType.HYDRO,
    'LARJI': GenType.HYDRO,
    'BASSI': GenType.HYDRO,
    'MALANA': GenType.HYDRO,  # http://globalenergyobservatory.org/geoid/44638
    'ANDHRA': GenType.HYDRO,
    'GHANVI': GenType.HYDRO,  # GANVI in type source
    # https://www.ejatlas.org/conflict/kashang-hydroelectricity-project
    'KASHANG': GenType.HYDRO,
    'MICROP/HMONITORED': GenType.UNKNOWN,  # No type source
    'IPPSP/HMONITORED': GenType.UNKNOWN,  # No type source
    'MICROP/HUNMONITORED': GenType.UNKNOWN,  # No type source
    # Plants in (B1)ISGS(HPSLDC WEB PORTAL) table:
    'BSIUL': GenType.HYDRO,  # BAIRASIUL HEP in type source.
    'CHAMERA1': GenType.HYDRO,
    'CHAMERA2': GenType.HYDRO,
    'CHAMERA3': GenType.HYDRO,
    'PARBATI3': GenType.HYDRO,
    'NJPC': GenType.HYDRO,  # NATHPA JHAKRI HEP in type source.
    'RAMPUR': GenType.HYDRO,
    'KOLDAM': GenType.HYDRO,
}


def fetch_production(zone_key=ZONE_KEY, session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    r = session or requests.session()
    if target_datetime is None:
        url = DATA_URL
    else:
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')
    res = r.get(url)
    assert res.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={}'.format(
                                       zone_key, url)
    soup = BeautifulSoup(res.text, 'html.parser')
    return {
        'zoneKey': ZONE_KEY,
        'datetime': arrow.now(TZ).datetime,
        'production': combine_gen(get_state_gen(soup), get_isgs_gen(soup)),
        'source': url
    }

    # TODO: Below is used for testing, remove once parser complete.
    # with open('/tmp/hpdata.txt', 'w') as text_file:
    #     text_file.write(res.text)

    # with open('/tmp/hpdata.txt', 'r') as text_file:
    #     soup = BeautifulSoup(text_file, 'html.parser')
    #     return {
    #         'zoneKey': ZONE_KEY,
    #         'datetime': arrow.now(TZ).datetime,
    #         'production': combine_gen(get_state_gen(soup), get_isgs_gen(soup)),
    #         'source': url
    #     }


def get_state_gen(soup):
    """Gets the total generation by type from state powerplants (MW).
    Data is from the table titled GENERATION OF HP(Z)"""
    table_name = 'GENERATION OF HP(Z)'
    gen = {GenType.HYDRO.value: 0.0, GenType.UNKNOWN.value: 0.0}
    # Read all rows except the last (Total).
    for row in get_table_rows(soup, 'table_5', table_name)[:-1]:
        try:
            cols = row.find_all('td')
            gen_type = get_gen_type(cols[0].text)
            gen[gen_type.value] += float(cols[1].text)
        except (AttributeError, IndexError, ValueError):
            raise Exception(
                'Error importing data from row: {}'.format(row))
    return gen


def get_isgs_gen(soup):
    """Gets the total generation by type from ISGS powerplants (MW).
    ISGS means Inter-State Generating Station: one owned by multiple states.
    Data is from the table titled (B1)ISGS(HPSLDC WEB PORTAL)"""
    table_name = '(B1)ISGS(HPSLDC WEB PORTAL)'
    gen = {GenType.HYDRO.value: 0.0, GenType.UNKNOWN.value: 0.0}
    # Read all rows except the first (headers) and last two (OTHERISGS and Total).
    for row in get_table_rows(soup, 'table_4', table_name)[1:-2]:
        try:
            cols = row.find_all('td')
            if not cols[0].has_attr('class'):
                # Ignore COMPANY column.
                del cols[0]
            gen_type = get_gen_type(cols[0].text)
            gen[gen_type.value] += float(cols[2].text)
        except (AttributeError, IndexError, ValueError):
            raise Exception(
                'Error importing data from row: {}'.format(row))
    return gen


def get_table_rows(soup, container_class, table_name):
    """Gets the table rows in the div identified by the provided class."""
    try:
        rows = soup.find('div', class_=container_class).find(
            'tbody').find_all('tr')
        if len(rows) == 0:
            raise ValueError
        return rows
    except (AttributeError, ValueError):
        raise Exception('Error reading table {}'.format(table_name))


def get_gen_type(desc):
    """Gets the generation type for the plant described by the given
    description string. Raises an error if the description is not recognised."""
    for plant_type in PLANT_NAMES_TO_TYPES.items():
        if plant_type[0] in desc.upper():
            return plant_type[1]
    raise ValueError


def combine_gen(gen1, gen2):
    """Combines two dictionaries of generation data.
    Currently only does Hydro and Unknown as there are
    no other types in the data source."""
    return {
        GenType.HYDRO.value: round(gen1[GenType.HYDRO.value] + gen2[GenType.HYDRO.value], 2),
        GenType.UNKNOWN.value: round(gen1[GenType.UNKNOWN.value] +
                                     gen2[GenType.UNKNOWN.value], 2)
    }


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
