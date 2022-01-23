#!/usr/bin/env python3

from typing import Union
import arrow
import re
import requests
from bs4 import BeautifulSoup
import logging
import datetime

TIMEZONE = 'Asia/Seoul'
REAL_TIME_URL = 'https://new.kpx.or.kr/powerinfoSubmain.es?mid=a10606030000'
PRICE_URL = 'https://new.kpx.or.kr/smpInland.es?mid=a10606080100&device=pc'
HYDRO_URL = 'https://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203'

#### Classification of New & Renewable Energy Sources ####
# Source: https://cms.khnp.co.kr/eng/content/563/main.do?mnCd=EN040101
# New energy: Hydrogen, Fuel Cell, Coal liquefied or gasified energy, and vacuum residue gasified energy, etc.
# Renewable: Solar, Wind power, Water power, ocean energy, Geothermal, Bio energy, etc.

# Gangneung hydro plant used only for peak load and backup
# sources for capacities: 
# 1) https://cms.khnp.co.kr/eng/content/566/main.do?mnCd=EN040201
# 2) https://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203
HYDRO_CAPACITIES = {
    # below is listed in 1)
    'Hwacheon': 108,
    'Chuncheon': 62.28,
    'Uiam': 48,
    'Cheongpyeong': 140.1,
    'Paldang': 120,
    'Chilbo': 35.4,
    'Boseonggang': 4.5,
    'Goesan': 2.8,
    'Gangrim': 0.48,
    'Gangneung': 82,
    # below is inferred from output in 2)
    'Anheung': 0.6,
    'Euiam': 14.8,
    'Seomjingang': 8
    }

######################################################
## Currently not used: Might be useful in the future # 
######################################################
# def timestamp_processor(timestamps, with_tz=False, check_delta=False):
#     """
#     Compares naive arrow objects, returning the average.
#     Optionally can determine if timestamps are too disparate to be used.
#     Returns an arrow object, with optional timezone.
#     """
#     if timestamps.count(timestamps[0]) == len(timestamps):
#         unified_timestamp = timestamps[0]
#     else:
#         average_timestamp = sum([arrow.get(ts).timestamp for ts in timestamps])/len(timestamps)
#         unified_timestamp = arrow.get(average_timestamp)

#     if check_delta:
#         for ts in timestamps:
#             delta = unified_timestamp - arrow.get(ts)
#             second_difference = abs(delta.total_seconds())

#             if second_difference > 3600:
#                 # more than 1 hour difference
#                 raise ValueError("""South Korea generation data is more than 1 hour apart,
#                                  saw {} hours difference""".format(second_difference/3600))

#     if with_tz:
#         unified_timestamp = unified_timestamp.replace(tzinfo=TIMEZONE)

#     return unified_timestamp
#
# def check_hydro_capacity(plant_name, value, logger) -> Union[bool, ValueError]:
#     """Makes sure that generation for each hydro plant isn't above listed capacity."""
#     try:
#         max_value = HYDRO_CAPACITIES[plant_name]
#     except KeyError:
#         if value != 0.0:
#             logger.warning('New hydro plant seen - {} - {}MW'.format(plant_name, value), extra={'key': 'KR'})
#         return True

#     if value > max_value:
#         logger.warning('{} reports {}MW generation with capacity of {}MW - discarding'.format(plant_name, value, max_value), extra={'key': 'KR'})
#         raise ValueError
#     else:
#         return True
# 
# def fetch_hydro(session, logger):
#     """Returns 2 element tuple in form (float, arrow object)."""
#     req = session.get(HYDRO_URL, verify=False)
#     soup = BeautifulSoup(req.content, 'html.parser')
#     table = soup.find("div", {"class": "dep02Sec"})

#     rows = table.find_all("tr")

#     plant_dts = []
#     total = 0.0
#     for row in rows:
#         sub_row = row.find("td")
#         if not sub_row:
#             # column headers
#             continue

#         plant_name = row.find("th").text

#         generation = sub_row.find("div", {"class": "tdCont alC"})
#         value = float(generation.text)

#         tag_dt = generation.findNext("td")
#         dt_naive = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm:ss")

#         try:
#             check_hydro_capacity(plant_name, value, logger)
#         except ValueError:
#             continue

#         plant_dts.append(dt_naive.datetime)
#         total += value

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
    url = REAL_TIME_URL

    response = r.get(url)
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, 'html.parser')
    consumption_title = soup.find("th", string=re.compile(r"\s*현재부하\s*"))
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
        url = REAL_TIME_URL
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

def fetch_price(zone_key='KR', session=None, target_datetime: datetime.datetime = None, logger=logging.getLogger(__name__)):
    
    # TODO: targeted datetime for last week should be possible
    if target_datetime:
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = PRICE_URL

    response = r.get(url)
    assert response.status_code == 200

    data = {
        'zoneKey': zone_key,
        'datetime': arrow.now(TIMEZONE).datetime,
        'currency': 'KRW',
        'price': 0.0,
        'source': 'new.kpx.or.kr',
    }

    soup = BeautifulSoup(response.text, 'html.parser')
    price_table = soup.find("table", {"class": "conTable tdCenter"})
    price_rows = price_table.find_all("tr")[1:]

    use_yesterday = False

    for i, row in enumerate(price_rows):
        today_price_value = float(row.find_all("td")[-1].text.replace(",", ""))
        if i == 0 and today_price_value == 0.0:
            # todays 1am price not published yet, use 12am price from second last column - aka yesterday
            use_yesterday = True
        elif not use_yesterday and today_price_value != 0.0:
            # todays price published
            data['price'] = today_price_value * 1000
            
            today_full_hour = datetime.datetime.now() - datetime.timedelta(hours= i + 1).replace(minute=0, second=0, microsecond=0)
            data['datetime'] = arrow.get(today_full_hour, TIMEZONE).datetime
            break
        elif use_yesterday and i == 23:
            # extracting 12am price from yesterday's column
            yesterday_price_value = float(row.find_all("td")[-2].text.replace(",", ""))
            data['price'] = yesterday_price_value * 1000

            today = datetime.datetime.now()
            yesterday = today - datetime.timedelta(days=0, hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond + 1)
            data['datetime'] = arrow.get(yesterday, TIMEZONE).datetime
            break

    return data


if __name__ == '__main__':
    print('fetch_price() -> ')
    print(fetch_price())

    print('fetch_consumption() -> ')
    print(fetch_consumption())

    print('fetch_production() -> ')
    print(fetch_production())