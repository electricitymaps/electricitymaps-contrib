#!/usr/bin/env python3

"""Parser for Croatian exchanges."""

import arrow
from pprint import pprint
import requests
import xml.etree.ElementTree as ET

xml_link = 'https://www.hops.hr/resources/razmjena.xml'


def get_xml_data(session=None):
    """Returns a request response body as bytes."""

    s = session or requests.Session()
    req = s.get(xml_link)

    return req.content


def xml_processor(raw_xml):
    """Returns a tuple containing a list of dictionaries and a arrow object."""

    xml_full = ET.fromstring(raw_xml)

    timestamp = xml_full.attrib['updateTime']
    dt_naive = arrow.get(timestamp, 'YYYY-MM-DD HH:mm:ss')
    dt_aware = dt_naive.replace(tzinfo='Europe/Belgrade')

    xml_values = []
    for child in xml_full:
        val = child.attrib
        xml_values.append(val)

    exchange_keys = ('Mađarska', 'Slovenija', 'Bosna i Hercegovina', 'Srbija i Crna Gora')
    exchange_data = [item for item in xml_values if item['key'] in exchange_keys]

    return exchange_data, dt_aware


def fetch_exchange(zone_key1, zone_key2, session=None, logger=None):
    """Requests the last known power exchange (in MW) between two countries
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
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

    # HOPS assigns negative values to exports.
    gxd = get_xml_data(session=None)
    processed_data = xml_processor(gxd)

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys == 'BA->HR':
        ba_exchange = next(
            item for item in processed_data[0] if item['key'] == "Bosna i Hercegovina")
        net_flow = float(ba_exchange['value'])
    elif sorted_zone_keys == 'HR->SI':
        si_exchange = next(item for item in processed_data[0] if item['key'] == "Slovenija")
        net_flow = -1 * float(si_exchange['value'])
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    exchange = {
        'sortedZoneKeys': sorted_zone_keys,
        'datetime': processed_data[1].datetime,
        'netFlow': net_flow,
        'source': 'hops.hr'
    }

    return exchange


if __name__ == '__main__':
    print('fetch_exchange(BA, HR)->')
    print(fetch_exchange('BA', 'HR'))
    print('fetch_exchange(HR, SI)->')
    print(fetch_exchange('HR', 'SI'))
