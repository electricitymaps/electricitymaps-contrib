#!/usr/bin/env python3

from requests import Session
from parsers.lib import web
from parsers.lib import countrycode
from parsers.lib import IN


def fetch_consumption(country_code='IN-CT', session=None):
    """Fetch Chhattisgarh consumption"""
    countrycode.assert_country_code(country_code, 'IN-CT')
    html = web.get_response_soup(country_code, 'http://117.239.199.203/csptcl/GEN.aspx', session)

    india_date_time = IN.read_datetime_from_span_id(html, 'L37', 'hh:m DD-MM-YY')

    demand_value = IN.read_value_from_span_id(html, 'L29')

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'consumption': demand_value,
        'source': 'cspc.co.in'
    }

    return data


def fetch_production(country_code='IN-CT', session=None):
    """Fetch Chhattisgarh production"""
    countrycode.assert_country_code(country_code, 'IN-CT')

    html = web.get_response_soup(country_code, 'http://117.239.199.203/csptcl/GEN.aspx', session)

    india_date_time = IN.read_datetime_from_span_id(html, 'L37', 'hh:m DD-MM-YY')

    korba_east_value = IN.read_value_from_span_id(html, 'L7')

    korba_west_value = IN.read_value_from_span_id(html, 'L13')

    dsmp_value = IN.read_value_from_span_id(html, 'L16')

    marwa_value = IN.read_value_from_span_id(html, 'L23')

    coal_value = round(korba_east_value + korba_west_value + dsmp_value + marwa_value, 2)

    bango_value = IN.read_value_from_span_id(html, 'L20')

    data = {
        'countryCode': country_code,
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
