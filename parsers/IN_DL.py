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

    # CCGT https://en.wikipedia.org/wiki/Pragati-III_Combined_Cycle_Power_Plant
    ccgt = read_value(prod_rows[2])

    # DMSWSL Unknown
    dmswsl = read_value(prod_rows[3])

    # EDWPL Unknown
    edwpl = read_value(prod_rows[4])

    # GT Unknown
    gt = read_value(prod_rows[5])

    # Pragati
    pragati = read_value(prod_rows[6])

    # TOWMP Waste?
    towmp = read_value(prod_rows[7])

    # Coal production
    coal = btps

    # Gas production
    gas = ccgt + pragati

    # Unknown production
    unknown_value = dmswsl + edwpl + gt + towmp

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'production': {
            'coal': coal,
            'gas': gas,
            'unknown': unknown_value
        },
        'source': 'delhisldc.org',
    }

    return data

def read_value(row):
    value = float(row.findAll('td')[2].text)
    return value if value >= 0.0 else 0.0



if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-DL', session)
    print fetch_consumption('IN-DL', session)
