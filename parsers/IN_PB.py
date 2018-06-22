#!/usr/bin/env python3

from requests import Session
from re import search, findall, M, S, I, sub
from arrow import utcnow, get
from bs4 import BeautifulSoup

from .lib.exceptions import ParserException
from .lib import web
from .lib import zonekey


def read_text_by_regex(regex, text):
    date_match = search(regex, text)
    if not date_match:
        raise ParserException('IN-PB', 'Not date_match')
    date_text = date_match.group(0)
    if not date_text:
        raise ParserException('IN-PB', 'Not date_text')
    return date_text


def fetch_production(zone_key='IN-PB', session=None, target_datetime=None, logger=None):
    """Fetch Punjab production"""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    zonekey.assert_zone_key(zone_key, 'IN-PB')
    response_text = web.get_response_text(
        zone_key, 'http://www.punjabsldc.org/pungenrealw.asp?pg=pbGenReal', session)

    time_text = read_text_by_regex('(\d+:\d+:\d+)', response_text)

    utc = utcnow().floor('hour')
    india_now = utc.to('Asia/Kolkata')
    time = get(time_text, 'HH:mm:ss')
    india_date = india_now.replace(hour=time.hour, minute=time.minute, second=time.second)
    if india_date > india_now:
        india_date.shift(days=-1)

    solar_match = search('Total Solar Generation = \d+', response_text)
    solar_text = solar_match.group(0)
    solar_value = findall('\d+', solar_text)[0]

    hydro_match = search('Total Hydro = \d+', response_text)
    hydro_text = hydro_match.group(0)
    hydro_value = findall('\d+', hydro_text)[0]

    thermal_match = search('Total Thermal = \d+', response_text)
    thermal_text = thermal_match.group(0)
    thermal_value = findall('\d+', thermal_text)[0]

    ipp_match = search('Total IPPs = \d+', response_text)
    ipp_text = ipp_match.group(0)
    ipp_value = findall('\d+', ipp_text)[0]

    data = {
        'zoneKey': zone_key,
        'datetime': india_date.datetime,
        'production': {
            'biomass': 0.0,
            'coal': round(float(thermal_value) + float(ipp_value), 2),
            'gas': 0.0,
            'hydro': float(hydro_value),
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': float(solar_value),
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': 0.0
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'punjasldc.org',
    }

    return data


def read_punjab_consumption_date(date_text, time_text, current):
    """ Read Punjab consumption date, format of this is not consistent.
        https://github.com/tmrowco/electricitymap/issues/854 """
    date_time_string = date_text + time_text + 'Asia/Kolkata'

    dates = []

    try:
        # Try to parse date string using MM/DD/YYYY format.
        mm_dd_yyyy_format_date = get(date_time_string, "MM/DD/YYYYHH:mm:ssZZZ")
        if mm_dd_yyyy_format_date and mm_dd_yyyy_format_date < current:
            dates.append(mm_dd_yyyy_format_date)
    except ValueError:
        pass

    try:
        # Try to parse date string using DD/MM/YYYY format.
        dd_mm_yyyy_format_date = get(date_time_string, "DD/MM/YYYYHH:mm:ssZZZ")
        if dd_mm_yyyy_format_date and dd_mm_yyyy_format_date < current:
            dates.append(dd_mm_yyyy_format_date)
    except ValueError:
        pass

    # Get correct date from parsed date array.
    if len(dates) > 0:
        return min(dates, key=lambda date: abs(date - current))
    else:
        raise Exception('IN-PB', 'Can''t read Punjab consumption date. DateTime String: {0}, Current Date: {1}'.format(date_time_string, current))


def fetch_consumption(zone_key='IN-PB', session=None, target_datetime=None, logger=None):
    """Fetch Punjab consumption"""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    zonekey.assert_zone_key(zone_key, 'IN-PB')
    response_text = web.get_response_text(
        zone_key, 'http://www.punjabsldc.org/nrrealw.asp?pg=nrGenReal',
                                          session)
    date_text = read_text_by_regex('(\d+/\d+/\d+)', response_text)
    time_text = read_text_by_regex('(\d+:\d+:\d+)', response_text)

    india_current_date = utcnow().to('Asia/Kolkata')
    india_date = read_punjab_consumption_date(date_text, time_text, india_current_date)

    punjab_match = search('<tr>(.*?)PUNJAB(.*?)</tr>', response_text, M|I|S).group(0)
    punjab_tr_text = findall('<tr>(.*?)</tr>', punjab_match, M|I|S)[1]

    punjab_text_font_cleaned = sub('<font(.*?)>', '', sub('</font>', '', punjab_tr_text))
    punjab_text_bold_cleaned = sub('<b>', '', sub('</b>', '', punjab_text_font_cleaned))
    punjab_text_paragraph_cleaned = sub('<p(.*?)>', '', sub('&nbsp;', '', punjab_text_bold_cleaned))

    punjab_soap = BeautifulSoup(punjab_text_paragraph_cleaned, 'html.parser')
    consumption_td = punjab_soap.findAll('td')[3]

    data = {
        'zoneKey': zone_key,
        'datetime': india_date.datetime,
        'consumption': float(consumption_td.text),
        'source': 'punjasldc.org'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-PB', session))
    print(fetch_consumption('IN-PB', session))
