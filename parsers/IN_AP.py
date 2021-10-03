from requests import Session
from .lib import zonekey, IN, web

URL = "https://core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx"
ZONE_KEY = 'IN-AP'
TIME_FORMAT = 'DD-MM-YYYY HH:mm'
SOURCE = 'core.ap.gov.in'
def fetch_production(zone_key=ZONE_KEY, session=None, target_datetime=None, logger=None):
    """Fetch Andhra Pradesh  production"""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    zonekey.assert_zone_key(zone_key, ZONE_KEY)

    html = web.get_response_soup(zone_key, URL, session)
    india_date = IN.read_datetime_from_span_id(html, 'MainContent_lblPowerStatusDate', TIME_FORMAT)

    hydro_value = IN.read_value_from_span_id(html, 'MainContent_lblHydel')
    gas_value = IN.read_value_from_span_id(html, 'MainContent_lblGas')
    wind_value = IN.read_value_from_span_id(html, 'MainContent_lblWind')
    solar_value = IN.read_value_from_span_id(html, 'MainContent_lblSolar')

    # All thermal centrals are considered coal based production
    # https://en.wikipedia.org/wiki/Power_sector_of_Andhra_Pradesh
    thermal_value = IN.read_value_from_span_id(html, 'MainContent_lblThermal')

    cgs_value = IN.read_value_from_span_id(html, 'MainContent_lblCGS')
    ipp_value = IN.read_value_from_span_id(html, 'MainContent_lblIPPS')

    data = {
        'zoneKey': zone_key,
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
        'source': SOURCE,
    }

    return data


def fetch_consumption(zone_key=ZONE_KEY, session=None, target_datetime=None, logger=None):
    """Fetch Andhra Pradesh consumption"""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    zonekey.assert_zone_key(zone_key, ZONE_KEY)

    html = web.get_response_soup(zone_key, URL, session)
    india_date = IN.read_datetime_from_span_id(html, 'MainContent_lblPowerStatusDate', TIME_FORMAT)

    demand_value = IN.read_value_from_span_id(html, 'MainContent_lblGridDemand')

    data = {
        'zoneKey': zone_key,
        'datetime': india_date.datetime,
        'consumption': demand_value,
        'source': SOURCE
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production(ZONE_KEY, session))
    print(fetch_consumption(ZONE_KEY, session))
