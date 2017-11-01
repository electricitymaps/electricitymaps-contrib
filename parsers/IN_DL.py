from requests import Session
from parsers.lib.exceptions import ParserException
from parsers.lib import web
from parsers.lib import countrycode
from parsers.lib import IN


def fetch_consumption(country_code='IN-DL', session=None):
    """Fetch Delhi consumption"""
    countrycode.assert_country_code(country_code, 'IN-DL')
    html = web.get_response_soup(country_code, 'http://www.delhisldc.org/Redirect.aspx', session)

    india_date_time = IN.read_datetime_from_span_id(html, 'DynamicData1_LblDate', 'DD-MMM-YYYY hh:mm:ss A')

    demand_value = IN.read_value_from_span_id(html, 'DynamicData1_LblLoad')

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'consumption': demand_value,
        'source': 'delhisldc.org'
    }

    return data


def fetch_production(country_code='IN-DL', session=None):
    """Fetch Karnataka  production"""
    countrycode.assert_country_code(country_code, 'IN-DL')

    html = web.get_response_soup(country_code, 'http://www.delhisldc.org/Redirect.aspx?Loc=0804', session)

    india_date_string = IN.read_text_from_span_id(html, 'ContentPlaceHolder3_ddgenco')
    india_date_time = IN.read_datetime_with_only_time(india_date_string, 'HH:mm:ss')

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'production': {
            'biomass': 0.0,
            'coal': 0.0,
            'gas': 0.0,
            'hydro': 0.0,
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': 0.0
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'delhisldc.org',
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-DL', session)
    print fetch_consumption('IN-DL', session)
