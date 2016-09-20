# -*- coding: utf-8 -*-

import arrow
import dateutil
import pandas as pd # In order to read excel

COUNTRY_CODE = 'HU'
TIME_ZONE = 'Europe/Budapest'

def fetch_HU():

    now = arrow.now(TIME_ZONE)

    # Fetch production
    url = ('http://rtdwweb.mavir.hu/webuser/ExportChartXlsIntervalServlet?' + 
        'fromDateXls=%s&fromTimeXls=T00%%3A00%%3A00&' % now.format('YYYY-MM-DD') + 
        'toDateXls=%s&toTimeXls=T00%%3A00%%3A00&' % now.replace(days=+1).format('YYYY-MM-DD') + 
        'resoulutionInput=15&unit=min&outputType=XLS&selectedTabId=tab9405&submitXls=')
    df_prod = pd.read_excel(url).dropna() # only keep non NaN value
    # Remove points in the future
    ix = map(lambda x: arrow.get(x, "YYYY.MM.DD HH:mm:ss").replace(tzinfo=dateutil.tz.gettz(TIME_ZONE)) < now, df_prod.dropna()[u'Időpont'])
    df_prod = df_prod.iloc[ix].iloc[-1] # Get the last

    # Fetch 
    url = ('http://rtdwweb.mavir.hu/webuser/ExportChartXlsIntervalServlet?' + 
        'fromDateXls=%s&fromTimeXls=T00%%3A00%%3A00&' % now.format('YYYY-MM-DD') + 
        'toDateXls=%s&toTimeXls=T00%%3A00%%3A00&' % now.replace(days=+1).format('YYYY-MM-DD') + 
        'resoulutionInput=15&unit=min&outputType=XLS&selectedTabId=tab5230&submitXls=')
    df_exchange = pd.read_excel(url).dropna() # only keep non NaN value
    # Remove points in the future
    ix = map(lambda x: arrow.get(x, "YYYY.MM.DD HH:mm:ss").replace(tzinfo=dateutil.tz.gettz(TIME_ZONE)) < now, df_exchange.dropna()[u'Időpont'])
    df_exchange = df_exchange.iloc[ix].iloc[-1] # Get the last
    
    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(df_prod[u'Időpont'], "YYYY.MM.DD HH:mm:ss").replace(
            tzinfo=dateutil.tz.gettz(TIME_ZONE)).datetime
    }
    obj['consumption'] = {
    }
    obj['exchange'] = {
        'SK': float(df_exchange[u'HU-SK mérés']),
        'AT': float(df_exchange[u'HU-AT mérés']),
        'HR': float(df_exchange[u'HU-HR mérés']),
        'RO': float(df_exchange[u'HU-RO mérés']),
        'RS': float(df_exchange[u'HU-RS mérés']),
        'UA': float(df_exchange[u'HU-UK mérés'])
    }
    obj['production'] = {
        'biomass': float(df_prod[u'Biomassza erőművek net.mérés (15p)']) + float(df_prod[u'Szemétégető erőművek net.mérés (15p)']),
        'coal': float(df_prod[u'Barnakőszén-lignit erőművek net.mérés (15p)']) + float(df_prod[u'Feketekőszén erőművek net.mérés (15p)']),
        'gas': float(df_prod[u'Gáz (fosszilis) erőművek net.mérés (15p)']),
        'hydro': float(df_prod[u'Folyóvizes erőmvek net.mérés (15p)']) + float(df_prod[u'Víztározós vízerőművek net.mérés (15p)']),
        'oil': float(df_prod[u'Olaj (fosszilis) erőművek net.mérés (15p)']),
        'nuclear': float(df_prod[u'Nukleáris erőművek net.mérés (15p)']),
        'solar': float(df_prod[u'Naperőművek net.mérés (15p)']),
        'wind': float(df_prod[u'Szárazföldi szélerőművek net.mérés (15p)'])
    }

    return obj

if __name__ == '__main__':
    print fetch_HU()
