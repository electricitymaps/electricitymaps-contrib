from requests import Session
from parsers import countrycode
from parsers import web
from parsers.lib import IN


def fetch_production(country_code='IN-AP', session=None):
    """Fetch Andhra Pradesh  production"""
    countrycode.assert_country_code(country_code, 'IN-AP')

    html = web.get_response_soup(country_code,
                                 'http://www.core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx', session)
    india_date = IN.read_datetime_from_span_id(html, 'lblPowerStatusDate', 'DD-MM-YYYY HH:mm')

    hydro_value = IN.read_value_from_span_id(html, 'lblHydel')
    gas_value = IN.read_value_from_span_id(html, 'lblGas')
    wind_value = IN.read_value_from_span_id(html, 'lblWind')
    solar_value = IN.read_value_from_span_id(html, 'lblSolar')

    # All thermal centrals are considered coal based production
    # https://en.wikipedia.org/wiki/Power_sector_of_Andhra_Pradesh
    thermal_value = IN.read_value_from_span_id(html, 'lblThermal')

    cgs_value = IN.read_value_from_span_id(html, 'lblCGS')
    ipp_value = IN.read_value_from_span_id(html, 'lblIPPS')

    data = {
        'countryCode': country_code,
        'datetime': india_date.datetime,
        'production': {
            'biomass': 0.0,
            'coal': thermal_value,
            'gas': gas_value,
            'hydro': hydro_value,
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': solar_value,
            'wind': wind_value,
            'geothermal': 0.0,
            'unknown': round(cgs_value + ipp_value, 2)
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'core.ap.gov.in',
    }

    return data


def fetch_consumption(country_code='IN-AP', session=None):
    """Fetch Andhra Pradesh consumption"""
    countrycode.assert_country_code(country_code, 'IN-AP')

    html = web.get_response_soup(country_code,
                                 'http://www.core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx', session)
    india_date = IN.read_datetime_from_span_id(html, 'lblPowerStatusDate', 'DD-MM-YYYY HH:mm')

    demand_value = IN.read_value_from_span_id(html, 'lblGridDemand')

    data = {
        'countryCode': country_code,
        'datetime': india_date.datetime,
        'consumption': demand_value,
        'source': 'core.ap.gov.in'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-AP', session)
    print fetch_consumption('IN-AP', session)

