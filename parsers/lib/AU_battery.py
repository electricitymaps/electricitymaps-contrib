#!/usr/bin/env python3

"""Parser for South Australia's 129MWh battery built by Tesla."""
import arrow
import json
import requests

# nemlog_url gets generation status in 5 min intervals.


def fetch_SA_battery(session=None):
    """
    Makes a request to the nemlog api for South Australia battery data.
    Returns a float or None.
    """

    today = arrow.now('Australia/Adelaide')
    current = today.format('YYYYMMDD')
    old = today.shift(days=-2).format('YYYYMMDD')
    nemlog_url = 'http://nemlog.com.au/api/unit/HPRL1/{}/{}/json'.format(old, current)

    s = session or requests.Session()
    req = s.get(nemlog_url)

    data = []
    for line in req.iter_lines():
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


if __name__ == '__main__':
    print('fetch_SA_battery() ->')
    print(fetch_SA_battery())
