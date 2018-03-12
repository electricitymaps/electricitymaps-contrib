#!/usr/bin/env python3

import datetime

import arrow
import requests
import pandas as pd

from .lib import AU_solar


timezone = 'Australia/Perth'

HOURS_TO_GET = 24


def fetch_production(zone_key='AUS-WA', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    session = session or requests.session()

    # explicitly request last 24 hours, to work around daybreaks in solar API
    allSolar = AU_solar.fetch_solar_all(session, HOURS_TO_GET)

    urlMeta = 'http://wa.aemo.com.au/aemo/data/wa/infographic/facility-meta.csv'
    dfFacilityMeta = pd.read_csv(urlMeta)
    dfFacilityMeta = dfFacilityMeta.drop(['PARTICIPANT_CODE', 'FACILITY_TYPE',
                                          'ALTERNATE_FUEL', 'GENERATION_TYPE',
                                          'YEAR_COMMISSIONED', 'YEAR_COMMISSIONED',
                                          'REGISTRATION_DATE', 'CAPACITY_CREDITS',
                                          'RAMP_UP', 'RAMP_DOWN', 'AS_AT'], axis=1)

    urlIntervals = 'http://wa.aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv'
    dfFacilityIntervals = pd.read_csv(urlIntervals)
    dfFacilityIntervals = dfFacilityIntervals.drop(['PARTICIPANT_CODE', 'PCT_ALT_FUEL',
                                                    'PEAK_MW', 'OUTAGE_MW', 'PEAK_OUTAGE_MW',
                                                    'INTERVALS_GENERATING', 'TOTAL_INTERVALS',
                                                    'PCT_GENERATING', 'AS_AT'], axis=1)

    dfCombined = pd.merge(dfFacilityMeta, dfFacilityIntervals, how='right', on='FACILITY_CODE')
    dfCombined['PERIOD'] = pd.to_datetime(dfCombined['PERIOD'])
    dfCombined['ACTUAL_MW'] = pd.to_numeric(dfCombined['ACTUAL_MW'])
    dfCombined['POTENTIAL_MWH'] = pd.to_numeric(dfCombined['POTENTIAL_MWH'])

    ts = dfCombined.PERIOD.unique()
    now = arrow.now().datetime

    result = []
    for timestamp in ts:
        # CSV gives us 48 hours of data (96 datapoints), but limit result to 24 hours
        timestampArrow = arrow.get(str(pd.Timestamp(timestamp)), 'YYYY-MM-DD HH:mm:ss').replace(tzinfo=timezone)
        timestampDate = timestampArrow.datetime
        if (timestampDate - now) > datetime.timedelta(hours=HOURS_TO_GET):
            continue

        tempdf = dfCombined.loc[dfCombined['PERIOD'] == timestamp]
        production = pd.DataFrame(tempdf.groupby('PRIMARY_FUEL').sum())
        production.columns = ['production', 'capacity']

        # capacity is specified to be "MWh" and the data points are very 30 minutes
        # so multiply by 2 to get MW value
        production['capacity'] *= 2

        production.ix['oil'] = production.ix['Distillate']
        production.drop('Distillate', inplace=True)
        production.ix['unknown'] = production.ix['Landfill Gas']
        production.drop('Landfill Gas', inplace=True)
        production.index = production.index.str.lower()

        rptData = production.to_dict()

        # get closest solar production data
        closestSolar = AU_solar.find_solar_nearest_time(allSolar, timestampDate)
        distributedSolarProduction = AU_solar.filter_solar_to_state(closestSolar, zone_key)

        if distributedSolarProduction:
            rptData['production']['solar'] = rptData['production'].get('solar', 0) + distributedSolarProduction

        data = {
            'zoneKey': zone_key,
            'production': rptData['production'],
            'capacity': rptData['capacity'],
            'datetime': timestampDate,
            'storage': {},
            'source': 'wa.aemo.com.au, pv-map.apvi.org.au',
        }

        result.append(data)

    return result


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print(fetch_production('AUS-WA'))
