#!/usr/bin/env python

import arrow
from bs4 import BeautifulSoup
from collections import defaultdict
from math import isnan
import numpy as np
import pandas as pd
import requests


#This parser gets hourly electricity generation data from oc.org.do for the Dominican Republic.
#The data is in MWh but since it is updated hourly we can view it as MW.
#Solar generation has no data available currently but multiple projects are planned/under construction.

url = 'http://184.168.74.190:81/ReportesGraficos/ReportePostdespacho.aspx'

total_mapping = {
                u'Total T\xe9rmico': 'Thermal',
                u'Total E\xf3lico': 'Wind',
                u'Total Hidroel\xe9ctrica': 'Hydro',
                'Total Generado': 'Generated'
                }

#Power plant types
#http://www.sie.gob.do/images/Estadisticas/MEM/GeneracionDiariaEnero2017/
#Reporte_diario_de_generacion_31_enero_2017_merged2.pdf

thermal_plants = {
                 u'AES ANDRES': 'gas',
                 u'BARAHONA CARBON': 'coal',
                 u'BERSAL': 'unknown',
                 u'CEPP 1': 'oil',
                 u'CEPP 2': 'oil',
                 u'CESPM 1': 'oil',
                 u'CESPM 2': 'oil',
                 u'CESPM 3': 'oil',
                 u'ESTRELLA DEL MAR 2 CFO': 'oil',
                 u'ESTRELLA DEL MAR 2 CGN': 'gas',
                 u'ESTRELLA DEL MAR 2 SFO': 'oil',
                 u'ESTRELLA DEL MAR 2 SGN': 'gas',
                 u'HAINA TG': 'oil',
                 u'INCA KM22': 'oil',
                 u'ITABO 1': 'coal',
                 u'ITABO 2': 'coal',
                 u'LA VEGA': 'oil',
                 u'LOS MINA 5': 'gas',
                 u'LOS MINA 6': 'gas',
                 u'LOS MINA 7': 'gas',
                 u'LOS OR\xcdGENES POWER PLANT FUEL OIL': 'oil',
                 u'LOS OR\xcdGENES POWER PLANT GAS NATURAL': 'gas',
                 u'METALDOM': 'oil',
                 u'MONTE PLATA SOLAR': 'solar',
                 u'MONTE RIO': 'oil',
                 u'PALAMARA': 'oil',
                 u'PIMENTEL 1': 'oil',
                 u'PIMENTEL 2': 'oil',
                 u'PIMENTEL 3': 'oil',
                 u'QUISQUEYA 1': 'gas',
                 u'QUISQUEYA 2': 'gas',
                 u'RIO SAN JUAN': 'oil',
                 u'SAN FELIPE': 'oil',
                 u'SAN FELIPE CC': 'gas',
                 u'SAN FELIPE VAP': 'oil',
                 u'SAN LORENZO 1': 'gas',
                 u'SAN PEDRO BIO-ENERGY': 'biomass',
                 u'SAN PEDRO VAPOR': 'oil',
                 u'SULTANA DEL ESTE': 'oil'
                 }


def get_data(session = None):
    """
    Makes a request to source url.
    Finds main table and creates a list of all table elements in unicode string format.
    Returns a list.
    """

    data = []
    s = session or requests.Session()
    data_req = s.get(url)
    soup = BeautifulSoup(data_req.content, 'lxml')

    tbs = soup.find("table", id="PostdespachoUnidadesTermicasGrid_DXMainTable")
    rows = tbs.find_all("td")

    for row in rows:
        num = row.getText().strip()
        data.append(unicode(num))

    return data


def floater(item):
    """
    Attempts to convert any item given to a float.  Returns item if it fails.
    """

    try:
        return float(item)
    except ValueError:
        return item


def chunker(big_lst):
    """
    Breaks a big list into a list of lists.  Removes any list with no data then turns remaining
    lists into key: value pairs with first element from the list being the key.
    Returns a dictionary.
    """
    
    chunks = [big_lst[x:x+27] for x in xrange(0, len(big_lst), 27)]

    #Remove the list if it contains no data.
    for chunk in chunks:
        if any(chunk) == True:
            continue
        else:
            chunks.remove(chunk)

    chunked_list = {words[0]:words[1:] for words in chunks}

    return chunked_list


def data_formatter(data):
    """
    Takes data and finds relevant sections.  Formats and breaks data into usable parts.
    Returns a nested dictionary.
    """

    find_thermal_index = data.index(u'GRUPO: T\xe9rmica')
    find_totals_index = data.index(u'Total T\xe9rmico')
    find_totals_end = data.index(u'Total Programado')

    ufthermal = data[find_thermal_index+3:find_totals_index-59]
    total_data = data[find_totals_index:find_totals_end]

    #Remove all comapany names.
    for val in ufthermal:
        if ':' in val:
            i = ufthermal.index(val)
            del ufthermal[i:i+3]
    
    formatted_thermal = chunker([floater(item) for item in ufthermal])
    mapped_totals = [total_mapping.get(x,x) for x in total_data]
    formatted_totals = chunker([floater(item) for item in mapped_totals])

    return {'totals': formatted_totals, 'thermal': formatted_thermal}


def data_parser(formatted_data):
    """
    Converts formatted data into a pandas dataframe.  Removes any empty rows.
    Returns a DataFrame.
    """

    dft = pd.DataFrame(formatted_data, index = [range(1,27)])

    dft = dft.drop(dft.index[[-1,-2]])
    dft = dft.replace(u'', np.nan)
    dft = dft.dropna(how = 'all')

    return dft


def thermal_production(df):
    """
    Takes DataFrame and finds thermal generation for current hour.
    Removes any non generating plants then maps plants to type.
    Sums type instances and returns a dictionary.    
    """

    #We only need the current hour.
    lastt = df.tail(1)

    #Create current plant output.
    tp = {}
    for item in list(df):
        v = lastt.iloc[0][item]
        tp[item] = v

    current_plants = {k: tp[k] for k in tp if not isnan(tp[k])}
    mapped_plants = [(thermal_plants[plant], val) for plant, val in current_plants.iteritems()]

    thermalDict = defaultdict(lambda: 0.0)

    #Sum values for duplicate keys.
    for key,val in mapped_plants:
        thermalDict[key] += val

    return thermalDict


def total_production(df):
    """
    Takes DataFrame and finds generation totals for current hour.
    Returns a dictionary.
    """

    #The Dominican Republic does not observe daylight savings time.
    find_hour = df.index[-1] 
    at = arrow.now('UTC-4')
    dt = (at.replace(hour = int(find_hour), minute = 0, second = 0)).datetime

    latest = df.tail(1)
    hydro = latest.iloc[0]['Hydro']
    wind = latest.iloc[0]['Wind']

    #Wind and hydro totals do not always update exactly on the new hour.
    #In this case we set them to None because they are unknown rather than zero.
    if isnan(wind):
        wind = None
    if isnan(hydro):
        hydro = None
    
    prod = {'wind': wind, 'hydro': hydro, 'datetime': dt}

    return prod


def fetch_production(country_code = 'DO', session = None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
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

    dat = data_formatter(get_data(session = None))
    tot = data_parser(dat['totals'])
    th = data_parser(dat['thermal'])
    thermal = thermal_production(th)
    total = total_production(tot)

    production_mix = {
      'countryCode': country_code,
      'datetime': total['datetime'],
      'production': {
          'biomass': thermal['biomass'],
          'coal': thermal['coal'],
          'gas': thermal['gas'],
          'hydro': total['hydro'],
          'nuclear': 0.0,
          'oil': thermal['oil'],
          'solar': None,
          'wind': total['wind'],
          'geothermal': 0.0,
          'unknown': thermal['unknown']
      },
      'storage': {
          'hydro': None,
      },
      'source': 'oc.org.do'
    }
    
    return production_mix
    

if __name__ ==  '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
