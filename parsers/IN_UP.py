#!/usr/bin/env python3
import json
from ast import literal_eval
import arrow
from requests import Session

from .lib import web


def fetch_data(country_code='IN-UP', session=None):

    time_now = arrow.now(tz='Asia/Kolkata')

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
        'total thermal up generation': 'unknown',
        'cogen-sent out': 'unknown',
        'solar generation': 'solar',
        'total up load/demand': 'demand'
    }

    response_objects = literal_eval(web.get_response_with_params(country_code, 'http://www.upsldc.org/real-time-data', session, params=html_params).text.lower())
    india_date = arrow.get(json.loads(list(response_objects[1].values())[0])['time_val'], 'M/D/YYYY h:m', tzinfo='Asia/Kolkata')

    value_map = {
        "date": india_date.datetime,
        "production": {
            "solar": None,
            "hydro": None,
            "geothermal": None,
            "wind": None,
            "gas": None,
            "coal": None,
            "unknown": None
        },
        "consumption": {
            "demand": None
        }
    }

    for obj in response_objects:
        val = json.loads(list(obj.values())[0])
        if 'point_desc' in val and val['point_desc'] in key_map:
            if key_map[val['point_desc']] == 'demand':
                value_map['consumption']['demand'] = float(val['point_val'])
            else:
                check = value_map['production'][key_map[val['point_desc']]]
                if check is None:
                    value_map['production'][key_map[val['point_desc']]] = float(val['point_val'])
                else:
                    value_map['production'][key_map[val['point_desc']]] += float(val['point_val'])

    return value_map


def fetch_production(country_code, session=None):
    """
    Method to get production data of Uttar Pradesh
    :param country_code:
    :param value_map:
    :return:
    """

    value_map = fetch_data(country_code, session)

    data = {
        'countryCode': country_code,
        'datetime': value_map.get('date'),
        'production': value_map.get('production'),
        'storage': {
            'hydro': None
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
        'consumption': value_map['consumption'].get('demand'),
        'source': 'upsldc.org'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-UP', session))
    print(fetch_consumption('IN-UP', session))
