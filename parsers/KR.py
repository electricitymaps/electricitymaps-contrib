#!/usr/bin/env python3

import arrow
import re
import requests
from bs4 import BeautifulSoup
from logging import getLogger


#LOAD
#get
#http://epsis.kpx.or.kr/epsisnew/selectMain.do
LOAD_URL = 'http://power.kpx.or.kr/powerinfo_en.php'

#then post
#http://epsis.kpx.or.kr/epsisnew/selectMainEpsMep.ajax


#HYDRO
HYDRO_URL = 'http://cms.khnp.co.kr/eng/realTimeMgr/water.do?mnCd=EN040203'

NUCLEAR_URLS = ['http://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302',
                'http://cms.khnp.co.kr/eng/hanbit/realTimeMgr/list.do?mnCd=EN03020202&brnchCd=BR0303',
                'http://cms.khnp.co.kr/eng/wolsong/realTimeMgr/list.do?mnCd=EN03020203&brnchCd=BR0305',
                'http://cms.khnp.co.kr/eng/hanul/realTimeMgr/list.do?mnCd=EN03020204&brnchCd=BR0304',
                'http://cms.khnp.co.kr/eng/saeul/realTimeMgr/list.do?mnCd=EN03020205&brnchCd=BR0312']
#NUCLEAR
# Nuclear is the sum of all these NPPs' units (22.5 GW):
#
#     Kori
#     http://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302
#     Hanbit
#     http://cms.khnp.co.kr/eng/hanbit/realTimeMgr/list.do?mnCd=EN03020202&brnchCd=BR0303
#     Wolsong
#     http://cms.khnp.co.kr/eng/wolsong/realTimeMgr/list.do?mnCd=EN03020203&brnchCd=BR0305
#     Hanul
#     http://cms.khnp.co.kr/eng/hanul/realTimeMgr/list.do?mnCd=EN03020204&brnchCd=BR0304
#     Saeul
#     http://cms.khnp.co.kr/eng/saeul/realTimeMgr/list.do?mnCd=EN03020205&brnchCd=BR0312
#
nuclear_url = 'http://cms.khnp.co.kr/eng/kori/realTimeMgr/list.do?mnCd=EN03020201&brnchCd=BR0302'

n2 = 'http://cms.khnp.co.kr/eng/saeul/realTimeMgr/list.do?mnCd=EN03020205&brnchCd=BR0312'
# <tr>
#
#
#
#
#
# 	                                		<th scope="row"><span>#2</span></th>
#
#
# 		                                <td headers="col1 col11"><div class="tdCont alC">682</div></td>
# 		                                <td headers="col1 col12"><div class="tdCont alC">2019-03-31 03:17</div></td>
# 		                                <td headers="col2 col21"><div class="tdCont alC">100</div></td>
# 		                                <td headers="col2 col22"><div class="tdCont alC">2019-03-31 03:17</div></td>
# 	                                </tr>


# <tr>
# 	                    <th scope="row" id="t1_row1"><span>Hwacheon</span></th>
# 	                    <td headers="t1_row1"><div class="tdCont alC">62.1</div></td>
# 	                    <td headers="t1_row1"><div class="tdCont alC">2019-03-31 03:00:02</div></td>
# 	                </tr>


#TODO capacity check
def fetch_hydro():
    # TODO datetime
    req = requests.get(HYDRO_URL)
    soup = BeautifulSoup(req.content, 'html.parser')
    table = soup.find("div", {"class": "dep02Sec"})

    rows = table.find_all("tr")
    #print(rows)

    plant_dts = []
    total = 0.0
    for row in rows:
        #print(row)
        sub_row = row.find("td")
        if not sub_row:
            # column headers
            continue
        generation = sub_row.find("div", {"class": "tdCont alC"})
        #print(generation)
        tag_dt = generation.findNext("td")
        dt_naive = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm:ss")
        plant_dts.append(dt_naive)
        total += float(generation.text)

    #if len(set(plant_dts))==1:
    if plant_dts.count(plant_dts[0]) == len(plant_dts):
        dt_aware = plant_dts[0]#.replace(tzinfo='Asia/Seoul')
        #print(dt)
    else:
        # TODO handle
        average_timestamp = sum([dt.timestamp for dt in plant_dts])/len(plant_dts)
        dt_aware = arrow.get(average_timestamp)#.replace(tzinfo='Asia/Seoul')


    return total, dt_aware


def fetch_nuclear(session=None):
    # TODO automate for each
    s=session or requests.Session()

    plant_dts = []
    total = 0.0
    #raw_rows = []
    for url in NUCLEAR_URLS:
        #print(url)
        req = s.get(url)#nuclear_url)
        soup = BeautifulSoup(req.content, 'html.parser')
        table = soup.find("tbody")
        #return table
        rows = table.find_all("tr")
        #raw_rows.append(rows)
    #print(raw_rows)
    # TODO datetime
    # TODO check output % effect
    # NOTE 1,059 style used
    # NOTE '0 ○' returned when plant shutdown
        for row in rows:
            #print(row)
            sub_row = row.find("td")
            generation = sub_row.find("div", {"class": "tdCont alC"})
            #print(generation)
            deformatted_generation = generation.text.replace(",", "")
            #print(deformatted_generation)
            try:
                total += float(deformatted_generation)
            except ValueError:
                #print('unit shutdown')
                continue

            tag_dt = sub_row.findNext("td")
            text_dt = tag_dt.find("div", {"class": "tdCont alC"})
            dt = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm")#.replace(tzinfo='Asia/Seoul')
            #print(deformatted_generation)
            #print(dt)
            plant_dts.append(dt)

    #print(plant_dts)
    if plant_dts.count(plant_dts[0]) == len(plant_dts):
        #dt = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm:ss").replace(tzinfo='Asia/Seoul')
        dt_aware = plant_dts[0]#.replace(tzinfo='Asia/Seoul')
        #print(dt)
    else:
        # TODO handle
        average_timestamp = sum([dt.timestamp for dt in plant_dts])/len(plant_dts)
        dt_aware = arrow.get(average_timestamp)#.replace(tzinfo='Asia/Seoul')
        #print(dt_aware)

    return total, dt_aware

# <div class="date">(2019.04.04. 19:20)</div>
def fetch_load():
    req = requests.get(LOAD_URL)
    soup = BeautifulSoup(req.content, 'html.parser')
    current_load = soup.find("th", text = re.compile('Current Load'))
    load_tag = current_load.findNext("td")
    load = float(load_tag.text.replace(",", ""))
    # TODO datetime needed

    tag_dt = soup.find("div", {"class": "date"})
    dt_aware = arrow.get(tag_dt.text, "(YYYY.MM.DD. HH:mm)")#.replace(tzinfo='Asia/Seoul')
    #print(dt)
    return load, dt_aware


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

    hydro, h_dt = fetch_hydro()

    nuclear, n_dt = fetch_nuclear()

    load, l_dt = fetch_load()

    #print(h_dt, n_dt, l_dt)

    plant_dts = [h_dt, n_dt, l_dt]

    print(plant_dts)

    if plant_dts.count(plant_dts[0]) == len(plant_dts):
        #dt = arrow.get(tag_dt.text, "YYYY-MM-DD HH:mm:ss").replace(tzinfo='Asia/Seoul')
        dt_aware = plant_dts[0].replace(tzinfo='Asia/Seoul')
        #print(dt)
    else:
        # TODO handle
        average_timestamp = sum([dt.timestamp for dt in plant_dts])/len(plant_dts)
        dt_aware = arrow.get(average_timestamp).replace(tzinfo='Asia/Seoul')
        #print(dt_aware)


    production = {
                  'production': {
                    'nuclear': nuclear,
                    'hydro': hydro,
                    'unknown': load - nuclear - hydro
                  },
                  'source': 'khnp.co.kr, kpx.or.kr',
                  'zoneKey': zone_key,
                  'datetime': dt_aware,
                  'storage': {}
                  }

    return production


if __name__ == '__main__':
    print('fetch_production() -> ')
    print(fetch_production())
