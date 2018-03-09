#!/usr/bin/env python3

import datetime

# The arrow library is used to handle datetimes
import arrow

# The request library is used to fetch content through HTTP
import requests

SOLAR_URL = 'http://pv-map.apvi.org.au/data/{date}'

"""
This script fetches distributed / small-scale / rooftop photovoltaic solar
generation data from the Australian PV Institute.

Note that this is *only* small-scale generation; the source http://pv-map.apvi.org.au/live
says "The APVI Live Map estimates exclude PV systems that are registered generators
in the NEM, as these are accounted for in AEMO's generation data."

Oddities and API notes:

The API returns datetimes in UTC, but oriented to Australian days.
A request to http://pv-map.apvi.org.au/data/2017-08-15 gives the first result
with timestamp "2017-08-14T18:00:00Z".

That seems a bit weird, but there is logic in it: that time corresponds to
2017-08-15 04:00 in Australian Eastern Standard Time.
04:00 AEST is before sunrise in the middle of the summer in all of Australia
(shortly before sunrise in the case of southerly Hobart).
Therefore, the API simply doesn't return data where it knows all generation
would be zero.

Also, the API stops updating with new timestamps once sun has set over Western Australia,
again to avoid zero entries.
"""


def _get_australian_date(days_in_past=0):
    utc_now = datetime.datetime.utcnow()

    if utc_now.hour >= 18:
        australian_date = utc_now + datetime.timedelta(days=1)
    else:
        australian_date = utc_now

    australian_date -= datetime.timedelta(days=days_in_past)

    # format as only Y-m-d
    return australian_date.strftime('%Y-%m-%d')


def fetch_solar_all(session, hours_in_the_past=2):
    data_url = SOLAR_URL.format(date=_get_australian_date())
    r = session.get(data_url)
    data = r.json()

    if data and 'output' in data and data['output']:
        production_data = data['output']

        first_timestamp = arrow.get(production_data[0]['ts'])

        if (arrow.utcnow() - first_timestamp).total_seconds() >= (hours_in_the_past * 60 * 60):
            return production_data
    else:
        production_data = []

    # If we got here, we want to get more data.
    # Requesting yesterday's data in the browser sometimes gives an HTTP 406 Unacceptable error,
    # but it's always worked in the script so far. Could double check and adjust
    # how many hours are fetched if it causes a problem in the future.
    data_url = SOLAR_URL.format(date=_get_australian_date(days_in_past=1))
    r = session.get(data_url)
    data = r.json()

    full_production_data = data['output'] + production_data

    return full_production_data


def find_solar_nearest_time(data, sought_time):
    """Finds value nearest to `sought_time`, as long as it's within 30 minutes."""
    max_timedelta_seconds = 30*60

    for datapoint in data:
        ts = arrow.get(datapoint['ts'])
        datapoint['timedelta'] = ts - sought_time
        datapoint['abs_timedelta'] = abs(datapoint['timedelta'].total_seconds())

    # find the closest match / smallest timedelta
    sorted_by_timedelta = list(sorted(data, key=lambda d: d['abs_timedelta']))
    closest_match = sorted_by_timedelta[0] if sorted_by_timedelta else None

    if closest_match and closest_match['abs_timedelta'] <= max_timedelta_seconds:
        return closest_match
    else:
        return None


def filter_solar_to_state(data, zone_key):
    data = data or {}  # handle being given None instead of data dict

    state_code = zone_key[4:]

    state_code_lowercase = state_code.lower()

    return data.get(state_code_lowercase, None)


def fetch_solar_for_date(zone_key, sought_time, session):
    """
    :return: int or None
    """
    if zone_key not in ('AUS-NSW', 'AUS-QLD', 'AUS-SA', 'AUS-TAS', 'AUS-VIC', 'AUS-WA'):
        raise Exception('Unrecognized zone_key {}'.format(zone_key))

    all_data = fetch_solar_all(session)

    closest_data = find_solar_nearest_time(all_data, sought_time)

    return filter_solar_to_state(closest_data, zone_key)


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_solar_for_date('AUS-NSW', arrow.utcnow(), requests.session()) ->")
    print(fetch_solar_for_date('AUS-NSW', arrow.utcnow(), requests.session()))
