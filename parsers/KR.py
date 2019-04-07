#!/usr/bin/env python3

import arrow
import re
import requests
from bs4 import BeautifulSoup
from logging import getLogger


LOAD_URL = 'http://power.kpx.or.kr/powerinfo_en.php'

HYDRO_URL = 'http://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203'

NUCLEAR_URLS = ['http://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302',
                'http://cms.khnp.co.kr/eng/hanbit/realTimeMgr/list.do?mnCd=EN03020202&brnchCd=BR0303',
                'http://cms.khnp.co.kr/eng/wolsong/realTimeMgr/list.do?mnCd=EN03020203&brnchCd=BR0305',
                'http://cms.khnp.co.kr/eng/hanul/realTimeMgr/list.do?mnCd=EN03020204&brnchCd=BR0304',
                'http://cms.khnp.co.kr/eng/saeul/realTimeMgr/list.do?mnCd=EN03020205&brnchCd=BR0312']


def timestamp_processor(timestamps, with_tz=False, check_delta=False):
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


#TODO capacity check
def fetch_hydro(session):
    req = session.get(HYDRO_URL)
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

        generation = sub_row.find("div", {"class": "tdCont alC"})
        tag_dt = generation.findNext("td")
        dt_naive = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm:ss")
        plant_dts.append(dt_naive)

        total += float(generation.text)

    dt = timestamp_processor(plant_dts)

    return total, dt


def fetch_nuclear(session):
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
    req = session.get(LOAD_URL)
    soup = BeautifulSoup(req.content, 'html.parser')

    current_load = soup.find("th", text = re.compile('Current Load'))
    load_tag = current_load.findNext("td")
    load = float(load_tag.text.replace(",", ""))

    tag_dt = soup.find("div", {"class": "date"})
    dt = arrow.get(tag_dt.text, "(YYYY.MM.DD. HH:mm)")

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

    s=session or requests.Session()

    hydro, hydro_dt = fetch_hydro(s)
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
                  'storage': {}
                  }

    return production


if __name__ == '__main__':
    print('fetch_production() -> ')
    print(fetch_production())
