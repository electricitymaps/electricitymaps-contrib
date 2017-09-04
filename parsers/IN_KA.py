from requests import Session
from parsers import web
from parsers import countrycode
from parsers import india


def fetch_production(country_code='IN-KA', session=None):
    """Fetch Karnataka  production"""
    countrycode.assert_country_code(country_code, 'IN-KA')

    html = web.get_response_soup(country_code, 'http://kptclsldc.com/StateGen.aspx', session)

    india_date_time = india.read_datetime_from_span_id(html, 'lbldate', 'D/M/YYYY h:mm:ss A')

    # State Production
    state_value = india.read_value_from_span_id(html, 'lblstategen')

    # CGS Production
    cgs_value = india.read_value_from_span_id(html, 'lblcgs')

    # NCEP Production
    ncep_value = india.read_value_from_span_id(html, 'lblncep')

    # RTPS Production: https://en.wikipedia.org/wiki/Raichur_Thermal_Power_Station
    rtps_value = india.read_value_from_span_id(html, 'lblrtptot')

    # BTPS Production: https://en.wikipedia.org/wiki/Bellary_Thermal_Power_station
    btps_value = india.read_value_from_span_id(html, 'lblbtptot')

    # YTPS Production: https://en.wikipedia.org/wiki/Yermarus_Thermal_Power_Station
    ytps_value = india.read_value_from_span_id(html, 'ytptot')

    # Coal Production
    coal_value = rtps_value + btps_value + ytps_value

    # Sharavati Production
    sharavati_value = india.read_value_from_span_id(html, 'lblshvytot')

    # Nagjhari Production
    nagjhari_value = india.read_value_from_span_id(html, 'lblngjtot')

    # Varahi Production
    varahi_value = india.read_value_from_span_id(html, 'lblvrhtot')

    # Kodsalli Production
    kodsalli_value = india.read_value_from_span_id(html, 'lblkdsltot')

    # Kadra Production
    kadra_value = india.read_value_from_span_id(html, 'lblkdrtot')

    # GERUSOPPA production
    gerusoppa_value = india.read_value_from_span_id(html, 'lblgrsptot')

    # JOG production
    jog_value = india.read_value_from_span_id(html, 'lbljogtot')

    # Hydro production
    hydro_value = sharavati_value + nagjhari_value + varahi_value + kodsalli_value + kadra_value + gerusoppa_value + jog_value

    # Unknown production
    unknown_value = state_value + cgs_value + ncep_value - coal_value - hydro_value

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'production': {
            'biomass': 0.0,
            'coal': round(coal_value, 2),
            'gas': 0.0,
            'hydro': round(hydro_value, 2),
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': round(unknown_value, 2)
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'kptclsldc.com',
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-KA', session)
