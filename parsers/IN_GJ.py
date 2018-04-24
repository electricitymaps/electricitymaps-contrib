#!/usr/bin/env python3

import re
from ast import literal_eval
from arrow import get
from requests import Session
from .lib import zonekey
from .lib import web
from .lib import IN
from .lib.validation import validate
from logging import getLogger
from operator import itemgetter


station_map = {
     "coal": ["Ukai(1-5)+Ukai6",
             "Wanakbori",
             "Gandhinagar",
             "Sikka(1-2)+Sikka(3-4)",
             "KLTPS(1-3)+KLTPS4",
             "SLPP(I+II)",
             "Akrimota",
             "TPAECo",
             "EPGL(I+II)",
             "Adani(I+II+III)",
             "BECL(I+II)",
             "CGPL "],
    "hydro": ["Ukai(Hydro)",
              "Kadana(Hydro)",
              "SSP(RBPH)"],
    "gas": ["Utran(Gas)(II)",
            "Dhuvaran(Gas)(I)+(II)",
            "GIPCL(I)",
            "GIPCL(II)",
            "GSEG(I+II)",
            "GPPC",
            "CLPI",
            "KAWAS",
            "Sugen+Unosgn",
            "JHANOR"],
    "nuclear": ["KAPP"]
}


def fetch_data(zone_key, session=None, logger=None):
    zonekey.assert_zone_key(zone_key, 'IN-GJ')

    solar_html = web.get_response_soup(
        zone_key, 'https://www.sldcguj.com/RealTimeData/GujSolar.php', session)
    wind_html = web.get_response_soup(
        zone_key, 'https://www.sldcguj.com/RealTimeData/wind.php', session)

    india_date = get(solar_html.find_all('tr')[0].text.split('\t')[-1].strip() + ' Asia/Kolkata', 'D-MM-YYYY H:mm:ss ZZZ')

    solar_value = float(literal_eval(solar_html.find_all('tr')[-1].find_all('td')[-1].text.strip()))
    wind_value = float(literal_eval(wind_html.find_all('tr')[-1].find_all('td')[-1].text.strip()))

    hydro_value = thermal_value = gas_value = coal_value = nuclear_value = unknown = 0.0

    value_map = {
        "date": india_date.datetime,
        "solar": solar_value,
        "hydro": hydro_value,
        "thermal": thermal_value,
        "wind": wind_value,
        "gas": gas_value,
        "coal": coal_value,
        "nuclear": nuclear_value,
        "unknown": unknown
    }

    cookies_params = {
        'ASPSESSIONIDSUQQQTRD': 'ODMNNHADJFGCMLFFGFEMOGBL',
        'PHPSESSID': 'a301jk6p1p8d50dduflceeg6l1'
    }

    rows = web.get_response_soup(zone_key, 'https://www.sldcguj.com/RealTimeData/RealTimeDemand.php',
                                 session).find_all('tr')

    for row in rows:
        elements = row.find_all('td')
        if len(elements) > 3:  # will find production rows
            v1, v2 = (re.sub(r'\s+', r'', x.text) for x in itemgetter(*[0, 3])(elements))
            energy_type = [k for k, v in station_map.items() if v1 in v]
            if len(energy_type) > 0:
                value_map[energy_type[0]] += float(literal_eval(v2))
            else:
                if 'StationName' in (v1, v2):  # meta data row
                    continue
                elif 'DSMRate' in v2:  # demand side management
                    continue
                else:
                    try:
                        logger.warning('Unknown fuel for station name: {}'.format(v1),
                            extra={'key': zone_key})
                        value_map['unknown'] += float(literal_eval(v2))
                    except (SyntaxError, ValueError) as e:
                        #handle eval failures which are likely to occur for new types
                        logger.warning('literal_eval failed on: {}'.format(v2), extra={'key': zone_key})
                        continue
        elif len(elements) == 3:  # will find consumption row
            v1, v2 = (re.sub(r'\s+', r'', x.text) for x in itemgetter(*[0, 2])(elements))
            if v1 == 'GujaratCatered':
                value_map['total consumption'] = float(literal_eval(v2.split('MW')[0]))

    return value_map


def fetch_production(zone_key='IN-GJ', session=None, target_datetime=None, logger=getLogger('IN-GJ')):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key: specifies which zone to get
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. The provided target_datetime is timezone-aware in UTC.
    logger: an instance of a `logging.Logger`; all raised exceptions are also logged automatically
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    value_map = fetch_data(zone_key, session, logger=logger)

    data = {
        'zoneKey': zone_key,
        'datetime': value_map['date'],
        'production': {
            'biomass': None,
            'coal': value_map['coal'],
            'gas': value_map['gas'],
            'hydro': value_map['hydro'],
            'nuclear': value_map['nuclear'],
            'oil': None,
            'solar': value_map['solar'],
            'wind': value_map['wind'],
            'geothermal': None,
            'unknown': value_map['unknown']
        },
        'storage': {
            'hydro': None
        },
        'source': 'sldcguj.com',
    }

    valid_data = validate(data, logger, remove_negative=True)

    return valid_data


def fetch_consumption(zone_key='IN-GJ', session=None, target_datetime=None, logger=getLogger('IN-GJ')):
    """
    Method to get consumption data of Gujarat
    :param zone_key:
    :param session:
    :return:
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    value_map = fetch_data(zone_key, session, logger=logger)

    data = {
        'zoneKey': zone_key,
        'datetime': value_map['date'],
        'consumption': value_map['total consumption'],
        'source': 'sldcguj.com'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-GJ', session))
    print(fetch_consumption('IN-GJ', session))
