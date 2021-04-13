
import logging
import datetime
import arrow
import requests


def fetch_production(zone_key='US-HI-OA', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given country.
    """
    r = session or requests.session()
    if target_datetime is None:
        url_date = arrow.get()
        url = 'https://www.islandpulse.org/api/mix?limit=1'
    else:
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        #url_date = arrow.get(target_datetime).to("Pacific/Honolulu")
        #url = 'https://www.islandpulse.org/api/mix?date={}'.format(url_date.date())

        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(url)

    obj = res.json()
    raw_data = obj[0]

    production = {
          'biomass': float(raw_data['Waste2Energy'] + raw_data['BioFuel']),
          'coal': float(raw_data['Coal']),
          'oil': float(raw_data['Fossil_Fuel']),
          'solar': float(raw_data['Solar']),
          'wind': float(raw_data['WindFarm'])
    }

    dt = arrow.get(raw_data['dateTime']).to(tz="Pacific/Honolulu").datetime

    data = {
        'zoneKey': zone_key,
        'production': production,
        'datetime': dt,
        'storage': {},
        'source': 'islandpulse.org'
    }

    return data

if __name__ == '__main__':
    print("fetch_production ->")
    print(fetch_production())
