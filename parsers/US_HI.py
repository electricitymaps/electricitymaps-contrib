#!/usr/bin/env python3

import logging
import datetime
import arrow
import requests

URL = 'https://www.islandpulse.org/api/mix?limit=1'

def fetch_production(zone_key='US-HI-OA', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or requests.session()
    if target_datetime is None:
        url_date = arrow.get()
    else:
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        #url_date = arrow.get(target_datetime).to("Pacific/Honolulu")
        #URL = 'https://www.islandpulse.org/api/mix?date={}'.format(url_date.date())

        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(URL)

    obj = res.json()
    raw_data = obj[0]

    production = {
          'biomass': float(raw_data['Waste2Energy'] + raw_data['BioFuel']),
          'coal': float(raw_data['Coal']),
          'oil': float(raw_data['Fossil_Fuel']),
          'solar': float(raw_data['Solar']),
          'wind': float(raw_data['WindFarm'])
    }

    # ensure the energy production data was captured less than 2 hours ago
    energy_dt = arrow.get(raw_data['dateTime']).to(tz="Pacific/Honolulu").datetime
    hi_dt = arrow.now("Pacific/Honolulu")
    diff = hi_dt - energy_dt
    if diff.total_seconds() > 7200:
        msg = ('Hawaii data is too old to use, '
               'parsed data timestamp was {0}.').format(energy_dt)
        logger.warning(msg, extra={'key': 'US-HI-OA'})
        return None

    data = {
        'zoneKey': zone_key,
        'production': production,
        'datetime': energy_dt,
        'storage': {},
        'source': 'islandpulse.org'
    }

    return data

if __name__ == '__main__':
    print("fetch_production ->")
    print(fetch_production())
