from requests import Session
from re import search, findall, M, S, I, sub
from arrow import utcnow, get
from bs4 import BeautifulSoup

from parsers.lib.exceptions import ParserException
from parsers.lib import web
from parsers.lib import countrycode


def fetch_production(country_code='IN-PB', session=None):
    """Fetch Punjab production"""
    countrycode.assert_country_code(country_code, 'IN-PB')
    response_text = web.get_response_text(country_code, 'http://www.punjabsldc.org/pungenrealw.asp?pg=pbGenReal', session)

    time_match = search('(\d+:\d+:\d+)', response_text)
    if not time_match:
        raise ParserException('IN-PB', 'Not time_match')
    time_text = time_match.group(0)
    if not time_text:
        raise ParserException('IN-PB', 'Not time_text')

    utc = utcnow()
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

    ipp_match = search('Total IPPs = \d+',response_text)
    ipp_text = ipp_match.group(0)
    ipp_value = findall('\d+', ipp_text)[0]

    data = {
        'countryCode': country_code,
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


def fetch_consumption(country_code='IN-PB', session=None):
    """Fetch Punjab consumption"""
    countrycode.assert_country_code(country_code, 'IN-PB')
    response_text = web.get_response_text(country_code, 'http://www.punjabsldc.org/nrrealw.asp?pg=nrGenReal',
                                          session)

    date_match = search('(\d+/\d+/\d+)', response_text)
    if not date_match:
        raise ParserException('IN-PB', 'Not date_match')
    date_text = date_match.group(0)
    if not date_text:
        raise ParserException('IN-PB', 'Not date_text')

    time_match = search('(\d+:\d+:\d+)', response_text)
    if not time_match:
        raise ParserException('IN-PB', 'Not time_match')
    time_text = time_match.group(0)
    if not time_text:
        raise ParserException('IN-PB', 'Not time_text')

    india_date_time = date_text + time_text + 'Asia/Kolkata'
    india_date = get(india_date_time, 'DD/MM/YYYYHH:mm:ssZZZ')

    punjab_match = search('<tr>(.*?)PUNJAB(.*?)</tr>', response_text, M|I|S).group(0)
    punjab_tr_text = findall('<tr>(.*?)</tr>', punjab_match, M|I|S)[1]

    punjab_text_font_cleaned = sub('<font(.*?)>', '', sub('</font>', '', punjab_tr_text))
    punjab_text_bold_cleaned = sub('<b>', '', sub('</b>', '', punjab_text_font_cleaned))
    punjab_text_paragraph_cleaned = sub('<p(.*?)>', '', sub('&nbsp;', '', punjab_text_bold_cleaned))

    punjab_soap = BeautifulSoup(punjab_text_paragraph_cleaned, 'html.parser')
    consumption_td = punjab_soap.findAll('td')[3]

    data = {
        'countryCode': country_code,
        'datetime': india_date.datetime,
        'consumption': float(consumption_td.text),
        'source': 'punjasldc.org'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-PB', session)
    print fetch_consumption('IN-PB', session)
