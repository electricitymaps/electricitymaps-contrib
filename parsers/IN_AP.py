#!/usr/bin/env python3

from requests import Session
from .lib import zonekey, IN, web


def fetch_production(zone_key='IN-AP', session=None, target_datetime=None, logger=None):
    """Fetch Andhra Pradesh  production"""
    if target_datetime:
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    zonekey.assert_zone_key(zone_key, 'IN-AP')

    html = web.get_response_soup(zone_key,
                                 'https://core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx', session)
    india_date = IN.read_datetime_from_span_id(
        html, 'MainContent_lblPowerStatusDate', 'DD-MM-YYYY HH:mm')

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
        'source': 'core.ap.gov.in',
    }

    return data


def fetch_consumption(zone_key='IN-AP', session=None, target_datetime=None, logger=None):
    """Fetch Andhra Pradesh consumption"""
    if target_datetime:
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    zonekey.assert_zone_key(zone_key, 'IN-AP')

    html = web.get_response_soup(zone_key,
                                 'https://core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx', session)
    india_date = IN.read_datetime_from_span_id(
<< << << < HEAD
        html, 'MainContent_lblPowerStatusDate', 'DD-MM-YYYY HH:mm')


== == == =
        html, 'lblPowerStatusDate', 'HH:mm DD-MM-YYYY')
>> >>>> > ea71daa4d01200302d25ccaa6ad8a1807de51ee3

    demand_value=IN.read_value_from_span_id(
        html, 'MainContent_lblGridDemand')

    data={
        'zoneKey': zone_key,
        'datetime': india_date.datetime,
        'consumption': demand_value,
        'source': 'core.ap.gov.in'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-AP', session))
    print(fetch_consumption('IN-AP', session))

lblPowerStatusDate
