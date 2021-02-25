#!/usr/bin/env python3

import arrow
import re
import requests
from bs4 import BeautifulSoup
from logging import getLogger

LOAD_URL = 'http://kpx.or.kr/eng/index.do'

HYDRO_URL = 'https://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203'

NUCLEAR_URLS = ['http://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302',
                'http://cms.khnp.co.kr/eng/hanbit/realTimeMgr/list.do?mnCd=EN03020202&brnchCd=BR0303',
                'http://cms.khnp.co.kr/eng/wolsong/realTimeMgr/list.do?mnCd=EN03020203&brnchCd=BR0305',
                'http://cms.khnp.co.kr/eng/hanul/realTimeMgr/list.do?mnCd=EN03020204&brnchCd=BR0304',
                'http://cms.khnp.co.kr/eng/saeul/realTimeMgr/list.do?mnCd=EN03020205&brnchCd=BR0312']

HYDRO_CAPACITIES = {'Hwacheon': 108,
                    'Chuncheon': 63,
                    'Anheung': 0.6,
                    'Uiam': 47,
                    'Cheongpyeong': 140,
                    'Paldang': 120,
                    'Goesan': 3,
                    'Chilbo': 35,
                    'Boseonggang': 4.5
                    }

# Gangneung hydro plant used only for peak load and backup, capacity info not available.
# Euiam hydro plant, no info available.


def timestamp_processor(timestamps, with_tz=False, check_delta=False):
    """Compares naive arrow objects, returning the average.
    Optionally can determine if timestamps are too disparate to be used.
    Returns an arrow object, with optional timezone.
    """
    if timestamps.count(timestamps[0]) == len(timestamps):
        unified_timestamp = timestamps[0]
    else:
        average_timestamp = sum([dt.timestamp for dt in timestamps])/len(timestamps)
        unified_timestamp = arrow.get(average_timestamp)

    if check_delta:
        for ts in timestamps:
            delta = unified_timestamp - arrow.get(ts)
            second_difference = abs(delta.total_seconds())

            if second_difference > 3600:
                # more than 1 hour difference
                raise ValueError("""South Korea generation data is more than 1 hour apart,
                                 saw {} hours difference""".format(second_difference/3600))

    if with_tz:
        unified_timestamp = unified_timestamp.replace(tzinfo='Asia/Seoul')

    return unified_timestamp


def check_hydro_capacity(plant_name, value, logger):
    """Makes sure that generation for each hydro plant isn't above listed capacity.
    Returns True or raises ValueError.
    """
    try:
        max_value = HYDRO_CAPACITIES[plant_name]
    except KeyError:
        if value != 0.0:
            logger.warning('New hydro plant seen - {} - {}MW'.format(plant_name, value), extra={'key': 'KR'})
        return True

    if value > max_value:
        logger.warning('{} reports {}MW generation with capacity of {}MW - discarding'.format(plant_name, value, max_value), extra={'key': 'KR'})
        raise ValueError
    else:
        return True


def fetch_hydro(session, logger):
    """Returns 2 element tuple in form (float, arrow object)."""
    req = session.get(HYDRO_URL, verify=False)
    soup = BeautifulSoup(req.content, 'html.parser')
    table = soup.find("div", {"class": "dep02Sec"})

    rows = table.find_all("tr")

    plant_dts = []
    total = 0.0
    for row in rows:
        sub_row = row.find("td")
        if not sub_row:
            # column headers
            continue

        plant_name = row.find("th").text

        generation = sub_row.find("div", {"class": "tdCont alC"})
        value = float(generation.text)

        tag_dt = generation.findNext("td")
        dt_naive = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm:ss")

        try:
            check_hydro_capacity(plant_name, value, logger)
        except ValueError:
            continue

        plant_dts.append(dt_naive)
        total += value

    dt = timestamp_processor(plant_dts)

    return total, dt


def fetch_nuclear(session):
    """Returns 2 element tuple in form (float, arrow object)."""
    plant_dts = []
    total = 0.0
    for url in NUCLEAR_URLS:
        req = session.get(url)
        soup = BeautifulSoup(req.content, 'html.parser')
        table = soup.find("tbody")
        rows = table.find_all("tr")

        for row in rows:
            sub_row = row.find("td")
            generation = sub_row.find("div", {"class": "tdCont alC"})

            # 1,059 style used
            deformatted_generation = generation.text.replace(",", "")

            try:
                total += float(deformatted_generation)
            except ValueError:
                # NOTE '0 ○' returned when plant shutdown
                continue

            tag_dt = sub_row.findNext("td")
            text_dt = tag_dt.find("div", {"class": "tdCont alC"})
            dt = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm")

            plant_dts.append(dt)

    dt = timestamp_processor(plant_dts)

    return total, dt


def fetch_load(session):
    """Returns 2 element tuple in form (float, arrow object)."""
    req = session.get(LOAD_URL)
    soup = BeautifulSoup(req.content, 'html.parser')

    load_tag = soup.find("div", {"class": "actual"})
    present_load = load_tag.find("dt", text=re.compile(r'Present Load'))
    value = present_load.find_next("dd").text.strip()

    # remove MW units
    num = value.split(" ")[0]

    load = float(num.replace(",", ""))

    date_tag = load_tag.find("p", {"class": "date"})
    despaced = re.sub(r'\s+', '', date_tag.text)

    # remove (day_of_week) part
    dejunked = re.sub(r'\(.*?\)', ' ', despaced)
    dt = arrow.get(dejunked, "YYYY.MM.DD HH:mm")

    return load, dt


def fetch_production(zone_key = 'KR', session=None, target_datetime=None, logger=getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
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
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    s = session or requests.Session()

    hydro, hydro_dt = fetch_hydro(s, logger)
    nuclear, nuclear_dt = fetch_nuclear(s)
    load, load_dt = fetch_load(s)

    generation_dts = [hydro_dt, nuclear_dt, load_dt]

    dt_aware = timestamp_processor(generation_dts, with_tz=True, check_delta=True)

    unknown = load - nuclear - hydro

    production = {
                  'production': {
                    'nuclear': nuclear,
                    'hydro': hydro,
                    'unknown': unknown
                  },
                   'source': 'khnp.co.kr, kpx.or.kr',
                   'zoneKey': zone_key,
                   'datetime': dt_aware.datetime,
                   'storage': {
                     'hydro': None,
                     'battery': None
                  }
                  }

    return production


if __name__ == '__main__':
    print('fetch_production() -> ')
    print(fetch_production())
