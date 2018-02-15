#!/usr/bin/env python3
import re
from ast import literal_eval
from operator import itemgetter
import json
from arrow import get
from requests import Session
import arrow
from parsers import countrycode
from parsers.lib import web


def fetch_data(country_code, session=None):
    countrycode.assert_country_code(country_code, 'IN-UP')

    time_now = arrow.now(tz='Asia/Kolkata')
    india_date = get(time_now, tzinfo='Asia/Kolkata').datetime
    # india_date = html.find_all('div', 'td-header', recursive=True)

    html_params = {
        'p_p_id': 'upgenerationsummary_WAR_UPSLDCDynamicDisplayportlet',
        'p_p_lifecycle': 2,
        'p_p_state': 'normal',
        'p_p_mode': 'view',
        'p_p_resource_id': 'realtimedata',
        'p_p_cacheability': 'cacheLevelPage',
        'p_p_col_id': 'column-1',
        'p_p_col_count': 1,
        '_upgenerationsummary_WAR_UPSLDCDynamicDisplayportlet_time': time_now,
        '_upgenerationsummary_WAR_UPSLDCDynamicDisplayportlet_cmd': 'realtimedata'
    }

    key_map = {
        'total hydro generation': 'hydro',
        'total thermal up generation': 'thermal',
        'cogen-sent out': 'unknown',
        'solar generation': 'solar',
        'total up load/demand': 'demand'
    }

    value_map = {
        "date": india_date,
        "solar": None,
        "hydro": None,
        "thermal": None,
        "wind": None,
        "gas": None,
        "coal": None
    }

    response_objects = literal_eval(session.get('http://www.upsldc.org/real-time-data', params=html_params).text.lower())
    for obj in response_objects:
        val = json.loads(list(obj.values())[0])
        if 'point_desc' in val and val['point_desc'] in key_map:
            value_map[key_map[val['point_desc']]] = float(val['point_val'])

    return value_map


def fetch_production(country_code, session=None):
    """
    Method to get production data of Uttar Pradesh
    :param country_code:
    :param value_map:
    :return:
    """

    value_map = fetch_data(country_code,session)

    data = {
        'countryCode': country_code,
        'datetime': value_map.get('date'),
        'production': {
            'biomass': value_map.get('biomass'),
            'coal': value_map.get('coal'),
            'gas': value_map.get('gas'),
            'hydro': value_map.get('hydro'),
            'nuclear': value_map.get('nuclear'),
            'oil': value_map.get('oil'),
            'solar': value_map.get('solar'),
            'wind': value_map.get('wind'),
            'thermal': value_map.get('thermal'),
            'unknown': value_map.get('unknown')
        },
        'storage': {
            'hydro': value_map.get('storage')
        },
        'source': 'upsldc.org',
    }

    return data


def fetch_consumption(country_code, session=None):
    """
    Method to get consumption data of Uttar Pradesh
    :param country_code
    :param value_map
    :return:
    """

    value_map = fetch_data(country_code, session)

    data = {
        'countryCode': country_code,
        'datetime': value_map.get('date'),
        'consumption': value_map.get('demand'),
        'source': 'upsldc.org'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-UP', session))
    print(fetch_consumption('IN-UP', session))
