#!/usr/bin/env python3
# coding=utf-8

import arrow
import re
import requests
from dateutil import parser as dparser
from dateutil import tz
from bs4 import BeautifulSoup

#URL of the power system summary: http://epso.am/poweren.htm
#URL of the detailled SCADA-page: http://epso.am/scada.htm

power_plant_mapping = {
    'var atom': 'nuclear', # atom = 'atomnaya elektro stantsiya'
    'var tes': 'gas',      # tes = 'termalnaya elektro stantsiya' - only gas in AM
    'var ges': 'hydro',    # ges = 'gidro elektro stantsiya'
    'var altern': 'hydro'  # altern = two hydro power plants according to SCADA data (middle row, right box)
    }

tie_line_mapping = {
    'var Lalvar': 'GE',
    'var ninoc': 'GE',
    'var alaver': 'GE',
    'var shin': 'AZ(AM)',
    'var arcakh': 'AZ(AM)',
    'var ahar': 'IR'
    }

other_variables_mapping = {
    'var cons': 'total production', #please note, this is an error of the variable name ('cons' is actually used for total production)
    'var peretok': 'total import/export', #positive = import, negative = export
    'var herc2': 'frequency',       #"hertz" ;)
    'var time2': 'timestamp',       #date is missing
    'sparum2': 'total consumption', #please note, this is an error of the variable name (probably means "production", but is used for consumption)
    }

soup_content_variables_mapping = {
    '[0]' : 'empty',
    '[1]' : 'Lalvar (GE)',
    '[2]' : 'ninoc (GE)',
    '[3]' : 'alaver (GE)',
    '[4]' : 'shin (AZ)',
    '[5]' : 'arcakh (AZ)',
    '[6]' : 'ahar (IR)',
    '[7]' : 'cons [total production]',
    '[8]' : ' altern',
    '[9]' : 'atom',
    '[10]' : 'tes',
    '[11]' : 'ges',
    '[12]' : 'peretok',
    '[13]' : 'herc2',
    '[14]' : 'time2',
    '[15]' : 'sparum2 []',
    '[16]' : 'empty',
    '[17]' : 'empty',
    }

def fetch_production(zone_key='AM', session=None, target_datetime=None, logger=None):
    r = session or requests.session()
    url = 'http://epso.am/poweren.htm'
    response = r.get(url)
    response.encoding = 'utf-8'
    html_doc = response.text
    soup = BeautifulSoup(html_doc, 'html.parser')

    data_string = soup.find(text=re.compile('var'))
    data_split = data_string.split('\r\n')

    gas_tes = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[10])
    gas_total = float(gas_tes[0])

    hydro_ges = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[11])
    hydro_altern = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[8])
    hydro_total = float(hydro_ges[0])+float(hydro_altern[0])

    nuclear_atom = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[9])
    nuclear_total = float(nuclear_atom[0])

    time_string = dparser.parse(data_split[14].split()[3],fuzzy=True)
    date_time = time_string.replace(tzinfo=tz.gettz('Asia/Yerevan'))

    #Operating solar, wind and biomass plants exist in small numbers, but are not reported yet
    data = {
        'zoneKey': zone_key,
        'datetime': date_time,
        'production': {
            'gas': gas_total,
            'hydro': hydro_total,
            'nuclear': nuclear_total,
            'coal': 0,
            'geothermal': 0,
            'oil': 0
            },
        'storage': {
            'hydro storage': 0,
            'battery storage': 0
            },
        'source': 'http://epso.am/poweren.htm'
    }

    return data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two countries
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """

    r = session or requests.session()
    url = 'http://epso.am/poweren.htm'
    response = r.get(url)
    response.encoding = 'utf-8'
    html_doc = response.text
    soup = BeautifulSoup(html_doc, 'html.parser')

    data_string = soup.find(text=re.compile('var'))
    data_split = data_string.split('\r\n')
    GE_1 = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[1])
    GE_2 = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[2])
    GE_3 = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[3])
    AZ_1 = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[4])
    AZ_2 = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[5])
    IR_1 = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", data_split[6])

    AM_AZ = float(AZ_1[0])+float(AZ_2[0])
    AM_GE = float(GE_1[0])+float(GE_2[0])+float(GE_3[0])
    AM_IR = float(IR_1[0])

    time_string = dparser.parse(data_split[14].split()[3],fuzzy=True)
    date_time = time_string.replace(tzinfo=tz.gettz('Asia/Yerevan'))
 
    if '->'.join(sorted([zone_key1, zone_key2])) == 'AM->AZ':
        AM_AZ_exchange = {
            'datetime': date_time,
            'netFlow': -1* AM_AZ,
            'source': 'http://epso.am/poweren.htm',
            'sortedZoneKeys': 'AM->AZ'
            }
        return AM_AZ_exchange
    elif '->'.join(sorted([zone_key1, zone_key2])) == 'AM->GE':
        AM_GE_exchange = {
            'datetime': date_time,
            'netFlow': -1 * AM_GE,
            'source': 'http://epso.am/poweren.htm',
            'sortedZoneKeys': 'AM-GE'
            }
        return AM_GE_exchange
    elif '->'.join(sorted([zone_key1, zone_key2])) == 'AM->IR':
        AM_IR_exchange = {
            'datetime': date_time,
            'netFlow': -1 * AM_IR,
            'source': 'http://epso.am/poweren.htm',
            'sortedZoneKeys': 'AM->IR'
            }
        return AM_IR_exchange
    else:
        raise NotImplementedError('This exchange pair is not implemented')

if __name__ == '__main__':
    print('fetch_production->')
    print(fetch_production())
    print('fetch_exchange(AM, AZ) ->')
    print(fetch_exchange('AM', 'AZ'))
    print('fetch_exchange(AM, GE) ->')
    print(fetch_exchange('AM', 'GE'))
    print('fetch_exchange(AM, IR) ->')
    print(fetch_exchange('AM', 'IR'))
