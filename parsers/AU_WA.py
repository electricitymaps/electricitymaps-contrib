import arrow
import requests
import json
import pandas as pd
import io
import dateutil
from collections import defaultdict
import datetime
 
def fetch_production(country_code=None, session=None):
    r = session or requests.session()
   
    urlMeta = 'http://wa.aemo.com.au/aemo/data/wa/infographic/facility-meta.csv'
    responseMeta = r.get(urlMeta)
    responseMetaContent = responseMeta.text
    dfFacilityMeta = pd.read_csv(io.StringIO(responseMetaContent.decode('utf-8')))
    dfFacilityMeta = dfFacilityMeta.drop(['PARTICIPANT_CODE','FACILITY_TYPE','ALTERNATE_FUEL','GENERATION_TYPE','YEAR_COMMISSIONED','YEAR_COMMISSIONED','REGISTRATION_DATE','CAPACITY_CREDITS','RAMP_UP','RAMP_DOWN','AS_AT'],axis=1)
        
    urlIntervals = 'http://wa.aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv'
    responseIntervals = r.get(urlIntervals)
    responseIntervalsContent = responseIntervals.text
    dfFacilityIntervals = pd.read_csv(io.StringIO(responseIntervalsContent.decode('utf-8')))
    dfFacilityIntervals = dfFacilityIntervals.drop(['PARTICIPANT_CODE','PCT_ALT_FUEL','PEAK_MW','OUTAGE_MW','PEAK_OUTAGE_MW','INTERVALS_GENERATING','TOTAL_INTERVALS','PCT_GENERATING','AS_AT'],axis=1)

    dfCombined = pd.merge(dfFacilityMeta,dfFacilityIntervals, how='right', on='FACILITY_CODE')
    dfCombined['PERIOD'] =  pd.to_datetime(dfCombined['PERIOD']) 
    dfCombined['ACTUAL_MW'] =  pd.to_numeric(dfCombined['ACTUAL_MW']) 
    dfCombined['POTENTIAL_MWH'] =  pd.to_numeric(dfCombined['POTENTIAL_MWH']) 
    
    ts = dfCombined.PERIOD.unique()
    
    rptData = defaultdict(float)
    returndata = {}
    for timestamp in ts:
        tz = 'Australia/Perth'
		
        dumpDate = arrow.get(str(pd.Timestamp(timestamp)), 'YYYY-MM-DD HH:mm:ss').replace(tzinfo=dateutil.tz.gettz(tz))
        #print dumpDate
        tempdf = dfCombined.loc[dfCombined['PERIOD'] == timestamp] 
        production = pd.DataFrame(tempdf.groupby('PRIMARY_FUEL').sum())
        production.columns = ['production', 'capacity']
        
        for key in production:    
            production['capacity'] *=  2
        production = production.round(1)
       
        production.ix['Oil'] = production.ix['Distillate']
        production.drop('Distillate', inplace=True)
        production.ix['Other'] = production.ix['Landfill Gas']
        production.drop('Landfill Gas', inplace=True)
                
        rptData = production.to_dict()
        data = {
            'countryCode': country_code,
            'production': rptData['production'],
            'capacity': rptData['capacity'],
            'datetime': dumpDate.datetime,
            'storage': {},
            'source': 'wa.aemo.com.au',
        }
        
    return data
      
   
if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print fetch_production('AUS-WA')   
