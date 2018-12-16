#!/usr/bin/env python3

"""Parser for South Australia's 129MWh battery built by Tesla."""
import arrow
import json
import requests


def get_unit_status(unit_code, start, end, session=None):
    # nemlog_url gets generation status in 5 min intervals.

    nemlog_url = 'http://nemlog.com.au/api/unit/{}/{}/{}/json'.format(
        unit_code, start, end)

    s = session or requests.Session()
    req = s.get(nemlog_url)
    data = []
    for line in req.iter_lines(decode_unicode=True):
        data.append(line)
    try:
        latest = json.loads(data[-1])
    except IndexError:
        # No data available.
        return None

    state = float(latest["SCADAVALUE"])

    # Source classifies charge/discharge opposite to EM.
    battery_status = -1 * state

    return battery_status


def fetch_SA_battery(session=None):
    """
    Makes a request for each battery to the nemlog api for South Australia
    battery data.
    Returns a float or None.
    """

    today = arrow.now('Australia/Adelaide')
    current = today.format('YYYYMMDD')
    old = today.shift(days=-2).format('YYYYMMDD')

    dalrymple_status = get_unit_status('DALNTHL1', old, current)
    hornsdale_status = get_unit_status('HPRL1', old, current)

    return sum(val if val is not None else 0 for val in
               [dalrymple_status, hornsdale_status])


if __name__ == '__main__':
    print('fetch_SA_battery() ->')
    print(fetch_SA_battery())
