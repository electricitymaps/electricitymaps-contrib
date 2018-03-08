#!/usr/bin/env python3

from requests import Session
from .lib import web
from .lib import zonekey
from .lib import IN


def fetch_consumption(zone_key='IN-CT', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    """Fetch Chhattisgarh consumption"""
    zonekey.assert_zone_key(zone_key, 'IN-CT')
    html = web.get_response_soup(zone_key, 'http://117.239.199.203/csptcl/GEN.aspx', session)

    india_date_time = IN.read_datetime_from_span_id(html, 'L37', 'hh:m DD-MM-YY')

    demand_value = IN.read_value_from_span_id(html, 'L29')

    data = {
        'zoneKey': zone_key,
        'datetime': india_date_time.datetime,
        'consumption': demand_value,
        'source': 'cspc.co.in'
    }

    return data


def fetch_production(zone_key='IN-CT', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    """Fetch Chhattisgarh production"""
    zonekey.assert_zone_key(zone_key, 'IN-CT')

    html = web.get_response_soup(zone_key, 'http://117.239.199.203/csptcl/GEN.aspx', session)

    india_date_time = IN.read_datetime_from_span_id(html, 'L37', 'hh:m DD-MM-YY')

    korba_east_value = IN.read_value_from_span_id(html, 'L7')

    korba_west_value = IN.read_value_from_span_id(html, 'L13')

    dsmp_value = IN.read_value_from_span_id(html, 'L16')

    marwa_value = IN.read_value_from_span_id(html, 'L23')

    coal_value = round(korba_east_value + korba_west_value + dsmp_value + marwa_value, 2)

    bango_value = IN.read_value_from_span_id(html, 'L20')

    data = {
        'zoneKey': zone_key,
        'datetime': india_date_time.datetime,
        'production': {
            'coal': coal_value,
            'hydro': bango_value
        },
        'source': 'cspc.co.in',
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-CT', session))
    print(fetch_consumption('IN-CT', session))
