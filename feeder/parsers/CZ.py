import arrow
import dateutil
import pandas as pd
import requests
from StringIO import StringIO

COUNTRY_CODE = 'CZ'
TIME_ZONE = 'Europe/Prague'

def fetch_CZ():
    now = arrow.now(TIME_ZONE)
    url = ('http://www.ceps.cz/_layouts/15/Ceps/_Pages/GraphData.aspx?mode=txt&' +
        'from=%s%%2012:00:00%%20AM&' % now.format('M/D/YYYY') +
        'to=%s%%2011:59:59%%20PM&' % now.replace(days=+1).format('M/D/YYYY') + 
        'hasinterval=False&sol=13&lang=ENG&agr=QH&fnc=AVG&ver=RT&para1=all&')
    data = pd.read_csv(StringIO(requests.get(url).text), sep=';', header=2).iloc[-1]

    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(data['Date'], "DD.MM.YYYY HH:mm").replace(
            tzinfo=dateutil.tz.gettz(TIME_ZONE)).datetime
    }
    obj['production'] = {
        'coal': data['TPP [MW]'],
        'gas': data['CCGT [MW]'],
        'nuclear': data['NPP [MW]'],
        'hydro': data['HPP [MW]'] + data['PsPP [MW]'],
        'solar': data['PVPP [MW]'],
        'wind': data['WPP [MW]'],
        'biomass': data['AltPP [MW]'],
        'unknown': data['ApPP [MW]'],
        'oil': 0,
    }
    obj['productionDatetime'] = arrow.get(data['Date'], "DD.MM.YYYY HH:mm").replace(
            tzinfo=dateutil.tz.gettz(TIME_ZONE)).datetime

    # Fetch exchanges
    url = ('http://www.ceps.cz/_layouts/15/Ceps/_Pages/GraphData.aspx?mode=txt&' +
        'from=%s%%2012:00:00%%20AM&' % now.format('M/D/YYYY') +
        'to=%s%%2011:59:59%%20PM&' % now.replace(days=+1).format('M/D/YYYY') + 
        'hasinterval=False&sol=8&lang=ENG&agr=HR&fnc=AVG&ver=RT&para1=all&')
    data = pd.read_csv(StringIO(requests.get(url).text), sep=';', header=2).iloc[-1]

    obj['exchange'] = {
        'PL': data['PSE Actual [MW]'],
        'SK': data['SEPS Actual [MW]'],
        'AT': data['APG Actual [MW]'],
        'DE': data['TenneT Actual [MW]'] + data['50HzT Actual [MW]']
    }
    obj['exchangeDatetime'] = arrow.get(data['Date'], "DD.MM.YYYY HH:mm").replace(
            tzinfo=dateutil.tz.gettz(TIME_ZONE)).datetime

    return obj

if __name__ == '__main__':
    print fetch_CZ()
