# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
# The pandas library is used to manipulate real time data
import pandas as pd

tz_gt = 'America/Guatemala'

MAP_GENERATION = {
    'coal': 'Turbina de Vapor',
    'gas': 'Turbina de Gas',
    'hydro': u'Hidroeléctrica',
    'oil': 'Motor Reciprocante',
    'solar': 'Fotovoltaica',
    'wind': u'Eólico',
    'geothermal': u'Geotérmica',
}


def fetch_production(country_code='GT', session=None):
    #output frame
    data = {
        'countryCode': country_code,
        'production': {},
        'storage': {},
        'source': 'www.amm.org.gt',
    }
    #Get actual date
    now = arrow.now(tz=tz_gt)
    #Define url to request
    formatted_date = now.format('DD/MM/YYYY')
    url_init = 'http://wl.amm.org.gt/AMM_LectorDePotencias-AMM_GraficasWs-context-root/jersey/CargaPotencias/graficaAreaScada/' 
    url = url_init + formatted_date
    #Request and rearange in DF
    r = session or requests.session()
    response = r.get(url)
    obj = response.json()
    obj_df = pd.DataFrame(obj)
    #Extract the corresponding hour
    h = str(now.hour)
    obj_h = obj_df[obj_df.hora == h]
    #Fill datetime variable
    data['datetime'] = now.replace(minute=0, second=0, microsecond=0).datetime   
    #First add 'Biomasa' and 'Biogas' together to make 'biomass' variable
    data['production']['biomass'] = obj_h[obj_h['tipo'] == 'Biomasa'].potencia.iloc[0] + obj_h[obj_h['tipo'] == 'Biogas'].potencia.iloc[0]
    #Then fill the other sources directly with the MAP_GENERATION frame
    for i_type in MAP_GENERATION.keys(): 
        data['production'][i_type] = obj_h[obj_h['tipo'] == MAP_GENERATION[i_type]].potencia.iloc[0]

    return data


def fetch_consumption(country_code='GT', session=None):
    #output frame
    data = {
        'countryCode': country_code,
        'consumption': {},
        'source': 'www.amm.org.gt',
    }
    #Get actual date
    now = arrow.now(tz=tz_gt)
    #Define url to request
    formatted_date = now.format('DD/MM/YYYY')
    url_init = 'http://wl.amm.org.gt/AMM_LectorDePotencias-AMM_GraficasWs-context-root/jersey/CargaPotencias/graficaAreaScada/' 
    url = url_init + formatted_date
    #Request and rearange in DF
    r = session or requests.session()
    response = r.get(url)
    obj = response.json()
    obj_df = pd.DataFrame(obj)
    #Extract the corresponding hour
    h = str(now.hour)
    obj_h = obj_df[obj_df.hora == h]
    #Fill datetime variable
    data['datetime'] = now.replace(minute=0, second=0, microsecond=0).datetime   
    #Fill consumption variable
    data['consumption'] = obj_h[obj_h['tipo'] == 'Dem SNI'].potencia.iloc[0]
    
    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print 'fetch_production() ->'
    print fetch_production()
    print 'fetch_consumption() ->'
    print fetch_consumption()
