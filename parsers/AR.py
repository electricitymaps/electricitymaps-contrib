#!/usr/bin/env python3

import itertools
import logging
import re
import string

import arrow
import requests
from bs4 import BeautifulSoup

from .const.AR_const import (
    CAMMESA_URL,
    EXCLUDED_PLANTS,
    H_URL,
    POWER_PLANT_TYPE,
    T_URL,
    TH_URL,
    TIE_MAPPING,
    URL
)

try:
    unicode  # Python 2
except NameError:
    unicode = str  # Python 3

# This parser gets hourly electricity generation data from portalweb.cammesa.com/Memnet1/default.aspx
# for Argentina.  Currently wind and solar power are small contributors and not monitored but this is
# likely to change in the future.

# Useful links.
# https://en.wikipedia.org/wiki/Electricity_sector_in_Argentina
# https://en.wikipedia.org/wiki/List_of_power_stations_in_Argentina
# http://globalenergyobservatory.org/countryid/10#
# http://www.industcards.com/st-other-argentina.htm


# Map of power plants to generation type.
# http://portalweb.cammesa.com/memnet1/revistas/estacional/base_gen.html


def webparser(req):
    """Takes content from webpage and returns all text as a list of strings"""

    soup = BeautifulSoup(req.content, 'html.parser')
    figs = soup.find_all("div", class_="r11")
    data_table = [unicode(tag.get_text()) for tag in figs]

    return data_table


def fetch_price(zone_key='AR', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """
    Requests the last known power price of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
      """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    s = session or requests.Session()
    price_req = s.get(CAMMESA_URL)
    psoup = BeautifulSoup(price_req.content, 'html.parser')
    find_price = psoup.find('td', class_="cssFuncionesLeft", align="left")

    try:
        price_text = find_price.getText()

        # Strip all whitespace and isolate number.  Convert to float.
        price_nws = "".join(price_text.split())
        lprice = price_nws.rpartition(':')[2]
        rprice = lprice.split('[')[0]
        price = float(rprice.replace(',', '.'))

    except (AttributeError, ValueError):
        # Price element not present or no price stated.
        price = None

    datetime = arrow.now('UTC-3').floor('hour').datetime

    data = {
        'zoneKey': zone_key,
        'currency': 'ARS',
        'datetime': datetime,
        'price': price,
        'source': 'portalweb.cammesa.com'
    }

    return data


def get_datetime(session=None):
    """
    Generation data is updated hourly.  Makes request then finds most recent hour available.
    Returns an arrow datetime object using UTC-3 for timezone and zero for minutes and seconds.
    """

    # Argentina does not currently observe daylight savings time.  This may change from year to year!
    # https://en.wikipedia.org/wiki/Time_in_Argentina
    s = session or requests.Session()
    rt = s.get(URL)
    timesoup = BeautifulSoup(rt.content, 'html.parser')
    find_hour = timesoup.find("option", selected="selected", value="1").getText()
    at = arrow.now('UTC-3').floor('hour')
    datetime = (at.replace(hour=int(find_hour), minute=0, second=0)).datetime

    return {'datetime': datetime}


def dataformat(junk):
    """Takes string data with only digits and returns it as a float."""

    formatted = []
    for item in junk:
        if not any(char in item for char in string.ascii_letters):
            item = float(item.replace(',', '.'))
        formatted.append(item)

    return formatted


def generation_finder(data, gen_type):
    """Finds all generation matching requested type in a list.
    Sums together and returns a float.
    """

    find_generation = [i + 2 for i, x in enumerate(data) if x == gen_type]
    generation_total = sum([data[i] for i in find_generation])

    return float(generation_total)


def get_thermal(session, logger):
    """
    Requests thermal generation data then parses and sorts by type.  Nuclear is included.
    Returns a dictionary.
    """

    # Need to persist session in order to get ControlID and ReportSession so we can send second request
    # for table data.  Both these variables change on each new request.
    s = session or requests.Session()
    r = s.get(URL)
    pat = re.search("ControlID=[^&]*", r.text).group()
    spat = re.search("ReportSession=[^&]*", r.text).group()
    cid = pat.rpartition('=')[2]
    rs = spat.rpartition('=')[2]
    full_table = []

    # 'En Reserva' plants are not generating and can be ignored.
    # The table has an extra column on 'Costo Operativo' page which must be removed to find power generated correctly.

    pagenumber = 1
    reserves = False

    while not reserves:
        t = s.get(T_URL, params={'ControlID': cid, 'ReportSession': rs,
                                'PageNumber': '{}'.format(pagenumber)})
        text_only = webparser(t)
        if 'Estado' in text_only:
            for item in text_only:
                if len(item) == 1 and item in string.ascii_letters:
                    text_only.remove(item)
        if 'En Reserva' in text_only:
            reserves = True
            continue
        full_table.append(text_only)
        pagenumber += 1

    data = list(itertools.chain.from_iterable(full_table))
    formatted_data = dataformat(data)
    mapped_data = [POWER_PLANT_TYPE.get(x, x) for x in formatted_data]

    for idx, item in enumerate(mapped_data):
        try:
            # avoids including titles and headings
            if all((item.isupper(), item.isalnum(), item != 'MERCADO')):
                if item in EXCLUDED_PLANTS:
                    continue
                logger.warning(
                    '{} is missing from the AR plant mapping!'.format(item),
                    extra={'key': 'AR'})
                mapped_data[idx] = 'unknown'
        except AttributeError:
            # not a string....
            continue

    nuclear_generation = generation_finder(mapped_data, 'nuclear')
    oil_generation = generation_finder(mapped_data, 'oil')
    coal_generation = generation_finder(mapped_data, 'coal')
    biomass_generation = generation_finder(mapped_data, 'biomass')
    gas_generation = generation_finder(mapped_data, 'gas')
    unknown_generation = generation_finder(mapped_data, 'unknown')

    if unknown_generation < 0.0:
        unknown_generation = 0.0

    return {'gas': gas_generation,
            'nuclear': nuclear_generation,
            'coal': coal_generation,
            'unknown': unknown_generation,
            'oil': oil_generation,
            'biomass': biomass_generation}


def get_hydro_and_renewables(session, logger):
    """Requests hydro generation data then parses into a usable format.
    There's sometimes solar and wind plants included in the data.
    Returns a dictionary."""

    s = session or requests.Session()
    r = s.get(H_URL)
    pat = re.search("ControlID=[^&]*", r.text).group()
    spat = re.search("ReportSession=[^&]*", r.text).group()
    cid = pat.rpartition('=')[2]
    rs = spat.rpartition('=')[2]
    full_table = []

    pagenumber = 1
    reserves = False

    while not reserves:
        t = s.get(TH_URL, params={'ControlID': cid, 'ReportSession': rs,
                                 'PageNumber': '{}'.format(pagenumber)})
        text_only = webparser(t)
        if 'En Reserva' in text_only:
            reserves = True
            continue
        full_table.append(text_only)
        pagenumber += 1

    data = list(itertools.chain.from_iterable(full_table))
    formatted_data = dataformat(data)
    mapped_data = [POWER_PLANT_TYPE.get(x, x) for x in formatted_data]

    for idx, item in enumerate(mapped_data):
        try:
            # avoids including titles and headings
            if all((item.isupper(), item.isalnum(), item != 'MERCADO')):
                if item in EXCLUDED_PLANTS:
                    continue
                logger.warning(
                    '{} is missing from the AR plant mapping!'.format(item),
                    extra={'key': 'AR'})
                mapped_data[idx] = 'unknown'
        except AttributeError:
            # not a string....
            continue

    hydro_generation = generation_finder(mapped_data, 'hydro')
    solar_generation = generation_finder(mapped_data, 'solar')
    wind_generation = generation_finder(mapped_data, 'wind')
    unknown_generation = generation_finder(mapped_data, 'unknown')
    hydro_storage_generation = generation_finder(mapped_data, 'hydro_storage')

    return {'hydro': hydro_generation,
            'wind': wind_generation,
            'solar': solar_generation,
            'unknown': unknown_generation,
            'hydro_storage': hydro_storage_generation}


def fetch_production(zone_key='AR', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    target_datetime: if we want to parser for a specific time and not latest
    logger: where to log useful information
    Return:
    A dictionary in the form:
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
    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    gdt = get_datetime(session=None)
    thermal = get_thermal(session, logger)
    hydro = get_hydro_and_renewables(session, logger)

    # discharging is given positive value in data, opposite to EM
    hydro_storage = hydro.pop('hydro_storage')
    if hydro_storage == 0.0:
        em_hydro_storage = hydro_storage
    else:
        em_hydro_storage = hydro_storage*-1

    unknown = thermal.pop('unknown') + hydro.pop('unknown')
    production = {**hydro, **thermal}
    production['unknown'] = unknown

    production_mix = {
        'zoneKey': zone_key,
        'datetime': gdt['datetime'],
        'production': production,
        'storage': {
            'hydro': em_hydro_storage,
        },
        'source': 'portalweb.cammesa.com'
    }

    return production_mix


def direction_finder(direction, exchange):
    """
    Uses the 'src' attribute of an "img" tag to find the
    direction of flow. In the data source small arrow images
    are used to show flow direction.
    """

    if direction == "/uflujpot.nsf/f90.gif":
        # flow from Argentina
        return 1
    elif direction == "/uflujpot.nsf/f270.gif":
        # flow to Argentina
        return -1
    else:
        raise ValueError('Flow direction for {} cannot be determined, got {}'.format(exchange, direction))


def tie_finder(exchange_url, exchange, session):
    """
    Finds tie data using div tag style attribute.
    Returns a float.
    """

    req = session.get(exchange_url)
    soup = BeautifulSoup(req.text, 'html.parser')

    tie = soup.find("div", style = TIE_MAPPING[exchange])
    flow = float(tie.text)
    direction_tag = tie.find_next("img")
    direction = direction_finder(direction_tag['src'], exchange)

    netflow = flow*direction

    return netflow


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    zone_key1, zone_key2: specifies which exchange to get
    session: requests session passed in order to re-use an existing session,
      not used here due to difficulty providing it to pandas
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. The provided target_datetime is timezone-aware in UTC.
    logger: an instance of a `logging.Logger`; all raised exceptions are also logged automatically
    Return:
    A list of dictionaries in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    # Only hourly data is available.
    if target_datetime:
        lookup_time = arrow.get(target_datetime).floor('hour').format('DD/MM/YYYY HH:mm')
    else:
        current_time = arrow.now('UTC-3')
        if current_time.minute < 30:
            # Data for current hour seems to be available after 30mins.
            current_time = current_time.shift(hours=-1)
        lookup_time = current_time.floor('hour').format('DD/MM/YYYY HH:mm')

    sortedcodes = '->'.join(sorted([zone_key1, zone_key2]))

    if sortedcodes == 'AR->CL-SEN':
        base_url = 'http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Unifilar de NOA&'
    else:
        base_url = 'http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Tensiones y Flujos de Potencia&'

    exchange_url = base_url + lookup_time

    s = session or requests.Session()

    if sortedcodes == 'AR->UY':
        first_tie = tie_finder(exchange_url, 'UY_1', s)
        second_tie = tie_finder(exchange_url, 'UY_2', s)
        flow = first_tie + second_tie
    elif sortedcodes == 'AR->PY':
        flow = tie_finder(exchange_url, 'PY', s)
    elif sortedcodes == 'AR->CL-SEN':
        flow = tie_finder(exchange_url, 'CL-SEN', s)
    else:
        raise NotImplementedError('This exchange is not currently implemented')

    exchange = {
      'sortedZoneKeys': sortedcodes,
      'datetime': arrow.now('UTC-3').datetime,
      'netFlow': flow,
      'source': 'cammesa.com'
    }

    return exchange


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_exchange(AR, PY) ->')
    print(fetch_exchange('AR', 'PY'))
    print('fetch_exchange(AR, UY) ->')
    print(fetch_exchange('AR', 'UY'))
    print('fetch_exchange(AR, CL-SEN) ->')
    print(fetch_exchange('AR', 'CL-SEN'))
