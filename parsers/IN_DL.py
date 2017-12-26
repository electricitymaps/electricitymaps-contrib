#!/usr/bin/env python3

from requests import Session
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
    """Fetch Delhi production"""
    countrycode.assert_country_code(country_code, 'IN-DL')

    html = web.get_response_soup(country_code, 'http://www.delhisldc.org/Redirect.aspx?Loc=0804', session)

    india_date_string = IN.read_text_from_span_id(html, 'ContentPlaceHolder3_ddgenco')
    india_date_time = IN.read_datetime_with_only_time(india_date_string, 'HH:mm:ss')

    prod_table = html.find("table", {"id": "ContentPlaceHolder3_dgenco"})
    prod_rows = prod_table.findAll('tr')

    # BTPS https://en.wikipedia.org/wiki/Badarpur_Thermal_Power_Station
    btps = read_value(prod_rows[1])

    # CCGT https://en.wikipedia.org/wiki/Pragati-III_Combined_Cycle_Power_Plant = Pragati-3
    ccgt = read_value(prod_rows[2])

    # DMSWSL (Delhi Municipal Solid Waste Solutions Limited): Garbage-to-electricity
    dmswsl = read_value(prod_rows[3])

    # EDWPL (East Delhi Waste Processing Company Limited): Garbage-to-electricity
    edwpl = read_value(prod_rows[4])

    # GT (Gas Turbine) https://en.wikipedia.org/wiki/IPGCL_Gas_Turbine_Power_Station
    gt = read_value(prod_rows[5])

    # Pragati https://en.wikipedia.org/wiki/Pragati-I_Combined_Cycle_Gas_Power_Station = Pragati-1
    pragati = read_value(prod_rows[6])

    # TOWMP (Timarpur Okhla Waste Management Company Pvt. Ltd.): Garbage-to-electricity
    towmp = read_value(prod_rows[7])

    # Coal production
    coal = btps

    # Gas production
    gas = ccgt + pragati + gt

    # Unknown production
    garbage = dmswsl + edwpl + towmp

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'production': {
            'coal': coal,
            'gas': gas,
            'biomass': garbage
        },
        'source': 'delhisldc.org',
    }

    return data

def read_value(row):
    value = float(row.findAll('td')[2].text)
    return value if value >= 0.0 else 0.0



if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-DL', session))
    print(fetch_consumption('IN-DL', session))
