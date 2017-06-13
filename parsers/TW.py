import arrow
import requests
import json
import pandas
import dateutil

def fetch_production(country_code='TW', session=None):
    
    r = session or requests.session()
    url = 'http://data.taipower.com.tw/opendata01/apply/file/d006001/001.txt'
    response = requests.get(url)
    content = response.content

    content = unicode(response.content,"UTF-8")
    data = json.loads(content)
    
    dumpDate = data['']
    prodData = data['aaData']
    
    tz = 'Asia/Taipei'
    dumpDate = arrow.get(dumpDate, 'YYYY-MM-DD HH:mm').replace(tzinfo=dateutil.tz.gettz(tz))
 
    objData = pandas.DataFrame(prodData);

    objData.columns = ['fueltype','name','capacity','output','percentage','additional']

    objData['fueltype'] = objData.fueltype.str.split('(').str[1]
    objData['fueltype'] = objData.fueltype.str.split(')').str[0]
    objData.drop('additional', axis=1, inplace=True)
    objData.drop('percentage', axis=1, inplace=True)
    
    objData = objData.convert_objects(convert_numeric=True)
    production = pandas.DataFrame(objData.groupby('fueltype').sum())
    production.columns = ['capacity','output']

    coal_production = production.ix['Coal'].output + production.ix['IPP-Coal'].output
    gas_production = production.ix['LNG'].output + production.ix['IPP-LNG'].output
    hydro_production = production.ix['Pumping Gen'].output - production.ix['Pumping Load'].output
    oil_production = production.ix['Oil'].output - production.ix['Diesel'].output
    production = production.drop(['LNG','IPP-LNG','IPP-Coal','Pumping Gen','Pumping Load','Diesel'])
    production.ix['Coal'].output = coal_production
    production.ix['Gas'] = [0,gas_production]
    production.ix['Hydro'] = [0,hydro_production]

    returndata = {
		'countryCode': country_code,
    'datetime': str(dumpDate.format('YYYY-MM-DDTHH:mm:ssZZ')),
		'production': {
			'coal': round(production.ix['Coal'].output,1),
            'gas': round(production.ix['Gas'].output,1),
            'oil': round(production.ix['Oil'].output,1),
        'hydro' : round(production.ix['Hydro'].output,1),
            'nuclear': round(production.ix['Nuclear'].output,1),
            'solar': round(production.ix['Solar'].output,1),
        'wind': round(production.ix['Wind'].output,1),
        'other': round(production.ix['Co-Gen'].output,1)
        },
        'storage': {},
        'source': 'http://www.taipower.com.tw/',
    }

    return returndata

if __name__ == '__main__':
    print fetch_production()
