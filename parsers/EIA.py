import datetime

import arrow
import requests

API_KEY = "b93a583eeed9d0ed324f3b21923af444"
DAY_AHEAD = {
    'US-SPP': 'EBA.SWPP-ALL.DF.H',
    'US-MISO': 'EBA.MISO-ALL.DF.H',
    'US-CA': 'EBA.CAL-ALL.DF.H',
    'US-NEISO': 'EBA.ISNE-ALL.DF.H',
    'US-NY': 'EBA.NYIS-ALL.DF.H',
    'US-PJM': 'EBA.PJM-ALL.DF.H',
}


def parse_response(url):
    r = requests.get(url)
    data = r.json()
    data = data['series'][0]

    values = []
    # data['description'] states 'Timestamps follow the ISO8601 standard
    # (https://en.wikipedia.org/wiki/ISO_8601). Hourly representations are
    # provided in Universal Time.'
    for dt, value in data['data']:
        dt = arrow.get(datetime.datetime.strptime(dt, '%Y%m%dT%HZ'),
                       'UTC').datetime
        values.append((dt, value))

    return values


def keep_after(values, target_time):
    min_time = arrow.get(target_time, tz='UTC').datetime
    return [(dt, v) for (dt, v) in values if min_time <= dt]


def fetch_consumption_forecast(zone_key, session=None, target_datetime=None,
                               logger=None):
    series_id = DAY_AHEAD[zone_key]
    url = "http://api.eia.gov/series/?api_key={api_key}&series_id=" \
          "{series_id}".format(api_key=API_KEY, series_id=series_id)

    values = parse_response(url)

    # we don't need to keep all values
    values = keep_after(values, target_datetime)

    return [{
        'zoneKey': zone_key,
        'datetime': dt,
        'value': value,
        'source': 'eia.org',
    } for dt, value in values]
