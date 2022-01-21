#!/usr/bin/env python3

from typing import Union
import arrow
import re
import requests
from bs4 import BeautifulSoup
import logging
import datetime

TIMEZONE = 'Asia/Seoul'

CONSUMPTION_URL = 'https://new.kpx.or.kr'
PRODUCTION_URL = 'https://new.kpx.or.kr/powerinfoSubmain.es?mid=a10606030000'

HYDRO_URL = 'https://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203'

# NUCLEAR_URLS = [
#     'https://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302',
#     'https://cms.khnp.co.kr/eng/hanbit/realTimeMgr/list.do?mnCd=EN03020202&brnchCd=BR0303',
#     'https://cms.khnp.co.kr/eng/wolsong/realTimeMgr/list.do?mnCd=EN03020203&brnchCd=BR0305',
#     'https://cms.khnp.co.kr/eng/hanul/realTimeMgr/list.do?mnCd=EN03020204&brnchCd=BR0304',
#     'https://cms.khnp.co.kr/eng/saeul/realTimeMgr/list.do?mnCd=EN03020205&brnchCd=BR0312'
# ]

# Gangneung hydro plant used only for peak load and backup, capacity info not available.
HYDRO_CAPACITIES = {
    'Hwacheon': 108,
    'Chuncheon': 62.28,
    'Anheung': 0.6,
    'Uiam': 46.5,
    'Cheongpyeong': 139.6,
    'Paldang': 120,
    'Goesan': 2.8,
    'Chilbo': 34.8,
    'Boseonggang': 4.5,
    'Euiam': 14.8,
    'Seomjingang': 8
    }


def timestamp_processor(timestamps, with_tz=False, check_delta=False):
    """
    Compares naive arrow objects, returning the average.
    Optionally can determine if timestamps are too disparate to be used.
    Returns an arrow object, with optional timezone.
    """
    if timestamps.count(timestamps[0]) == len(timestamps):
        unified_timestamp = timestamps[0]
    else:
        average_timestamp = sum([arrow.get(ts).timestamp for ts in timestamps])/len(timestamps)
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
        unified_timestamp = unified_timestamp.replace(tzinfo=TIMEZONE)

    return unified_timestamp


def check_hydro_capacity(plant_name, value, logger) -> Union[bool, ValueError]:
    """Makes sure that generation for each hydro plant isn't above listed capacity."""
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

        plant_dts.append(dt_naive.datetime)
        total += value

    dt = timestamp_processor(plant_dts)

    return total, dt


# def fetch_nuclear(session):
#     """Returns 2 element tuple in form (float, arrow object)."""
#     plant_dts = []
#     total = 0.0
#     for url in NUCLEAR_URLS:
#         req = session.get(url)
#         soup = BeautifulSoup(req.content, 'html.parser')

#         table = soup.find("tbody")
#         rows = table.find_all("tr")

#         for row in rows:

#             sub_row = row.find("td")
#             generation = sub_row.find("div", {"class": "tdCont alC"})

#             # 1,059 style used
#             deformatted_generation = generation.text.replace(",", "")

#             try:
#                 total += float(deformatted_generation)
#             except ValueError:
#                 # NOTE '0 ○' returned when plant shutdown
#                 continue

#             tag_dt = sub_row.findNext("td")
#             text_dt = tag_dt.find("div", {"class": "tdCont alC"})
#             dt = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm")

#             plant_dts.append(dt.datetime)

#     dt = timestamp_processor(plant_dts)

#     return total, dt

def fetch_consumption(
    zone_key="KR", session=None, target_datetime=None, logger=logging.getLogger(__name__)) -> dict:
    """
      Fetches consumption.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    url = CONSUMPTION_URL

    response = r.get(url)
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, 'html.parser')
    consumption_title = soup.find("h4", string=re.compile(r"\s*현재부하\s*"))
    consumption_val = float(consumption_title.find_next_sibling().text.split()[0].replace(",", ""))

    data = {
        'consumption': consumption_val,
        'datetime': arrow.now(TIMEZONE).datetime,
        'source': url,
        "zoneKey": zone_key,
    }

    return data

def fetch_production(zone_key='KR', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)) -> dict:
    """
    Requests the last known production mix (in MW) of a given country.
    """
    r = session or requests.session()
    if target_datetime is None:
        url = PRODUCTION_URL
    else:
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(url)
    assert res.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={}'.format(
                                       zone_key, url)

    soup = BeautifulSoup(res.text, 'html.parser')
    production_table = soup.find_all("table", {"class": "conTable tdCenter"})[3]

    rows = production_table.find_all("tr")[1:]

    data = {
      'zoneKey': 'KR',
      'datetime': arrow.now(TIMEZONE).datetime,
      'production': {
          'biomass': 0.0,
          'coal':0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': 0.0,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0,
      },
      'storage': {},
      'source': 'https://new.kpx.or.kr'
    }

    for i, row in enumerate(rows):
        row_values = row.find_all("td")
        row_datetime_values = [value[:-1] for value in row_values[0].text.split(" ")]
        production_values = [int("".join(value.text.split(","))) for value in row_values[1:]]

        if i+1 <= len(rows) - 1:
            next_row = rows[i+1]
            next_row_values = next_row.find_all("td")
            next_row_values = [int("".join(value.text.split(","))) for value in next_row_values[1:]]

            if not all(next_row_values):
                curr_prod_datetime_string = "-".join(row_datetime_values[:3]) + "T" + ":".join(row_datetime_values[3:]) + ":00"
                arw = arrow.get(curr_prod_datetime_string, "YYYY-MM-DDTHH:mm:ss", tzinfo=TIMEZONE)
                data["datetime"] = arw.datetime
                data["production"]["coal"] = production_values[3]
                data["production"]["gas"] = production_values[1]
                data["production"]["nuclear"] = production_values[4]
                data["production"]["unknown"] = production_values[2] + production_values[0]
                break

    return data


# def fetch_production(zone_key='KR', session=None, target_datetime=None, logger: logging.Logger = logging.getLogger(__name__)) -> dict:
#     """Requests the last known production mix (in MW) of a given zone."""
#     if target_datetime:
#         raise NotImplementedError('This parser is not yet able to parse past dates')

#     s = session or requests.Session()

#     # hydro, hydro_dt = fetch_hydro(s, logger)
#     # nuclear, nuclear_dt = fetch_nuclear(s)
#     # consumption = fetch_consumption(s)

#     generation_dts = [hydro_dt, nuclear_dt, consumption["datetime"]]

#     dt_aware = timestamp_processor(generation_dts, with_tz=True, check_delta=True)

#     unknown = consumption["consumption"] - nuclear - hydro

#     production = {
#                   'production': {
#                     'nuclear': nuclear,
#                     'hydro': hydro,
#                     'unknown': unknown
#                   },
#                    'source': 'khnp.co.kr, kpx.or.kr',
#                    'zoneKey': zone_key,
#                    'datetime': dt_aware.datetime,
#                    'storage': {
#                      'hydro': None,
#                      'battery': None
#                   }
#                   }

#     return production


if __name__ == '__main__':
    print('fetch_consumption() -> ')
    print(fetch_consumption())

    print('fetch_production() -> ')
    print(fetch_production())