import arrow
import dateutil
import pandas as pd # In order to read excel
import requests

COUNTRY_CODE = 'HU'
TIME_ZONE = 'Europe/Budapest'

def fetch_HU():

    now = arrow.now(TIME_ZONE)
    url = ('http://rtdwweb.mavir.hu/webuser/ExportChartXlsIntervalServlet?' + 
        'fromDateXls=%s&fromTimeXls=T00%%3A00%%3A00&' % now.format('YYYY-MM-DD') + 
        'toDateXls=%s&toTimeXls=T00%%3A00%%3A00&' % now.replace(days=+1).format('YYYY-MM-DD') + 
        'resoulutionInput=15&unit=min&outputType=XLS&selectedTabId=tab9405&submitXls=')
    df = pd.read_excel(url).dropna().iloc[-1] # Get the last non NaN value
    
    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(df[u'Időpont'], "YYYY.MM.DD HH:mm:ss").replace(
            tzinfo=dateutil.tz.gettz(TIME_ZONE)).datetime
    }
    obj['consumption'] = {
    }
    obj['exchange'] = {
    }
    obj['production'] = {
        'biomass': float(df[u'Biomassza erőművek net.mérés (15p)']) + float(df[u'Szemétégető erőművek net.mérés (15p)']),
        'coal': float(df[u'Barnakőszén-lignit erőművek net.mérés (15p)']) + float(df[u'Feketekőszén erőművek net.mérés (15p)']),
        'gas': float(df[u'Gáz (fosszilis) erőművek net.mérés (15p)']),
        'hydro': float(df[u'Folyóvizes erőmvek net.mérés (15p)']) + float(df[u'Víztározós vízerőművek net.mérés (15p)']),
        'oil': float(df[u'Olaj (fosszilis) erőművek net.mérés (15p)']),
        'nuclear': float(df[u'Nukleáris erőművek net.mérés (15p)']),
        'solar': float(df[u'Naperőművek net.mérés (15p)']),
        'wind': float(df[u'Szárazföldi szélerőművek net.mérés (15p)'])
    }

    return obj

if __name__ == '__main__':
    print fetch_HU()
