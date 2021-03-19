#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import arrow
import json
# The request library is used to fetch content through HTTP
import requests
import re

tz_bo = 'America/La_Paz'


def extract_xsrf_token(html):
  """Extracts XSRF token from the source code of the generation graph page"""
  return re.search(r'var ttoken = "([a-f0-9]+)";', html).group(1)


def template_response(zone_key, datetime, source):
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "hydro": 0.0,
            "unknown": 0, # Gas + Oil are mixed, so unknown for now
            "wind": 0
        },
        "storage": {},
        "source": source,
    }

def template_forecast_response(zone_key, datetime, source):
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "value": None,
        "source": source,
    }


def fetch_production(zone_key='BO', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """
    if target_datetime is not None:
        now = arrow.get(target_datetime)
    else:
        now = arrow.now(tz=tz_bo)

    r = session or requests.session()

    # Define actual and previous day (for midnight data).
    formatted_date = now.format('YYYY-MM-DD')

    # initial path for url to request
    url_init = 'https://www.cndc.bo/gene/dat/gene.php?fechag={0}'

    # XSRF token for the initial request
    xsrf_token = extract_xsrf_token(r.get("https://www.cndc.bo/gene/index.php").text)

    resp = r.get(url_init.format(formatted_date), headers={
        "x-csrf-token": xsrf_token
    })

    hour_rows = json.loads(resp.text.replace('ï»¿', ''))["data"]
    payload = []

    for hour_row in hour_rows:
        [hour, forecast, _total, thermo, hydro, wind, _unknown] = hour_row

        if target_datetime is None and hour > now.hour:
            continue

        if hour == 24:
            timestamp = now.shift(days=1)
        else:
            timestamp = now

        if target_datetime is not None and hour < 24:
            timestamp = timestamp.replace(hour=hour-1)


        hour_resp = template_response(zone_key, timestamp.datetime, "cndc.bo")
        hour_resp["production"]["unknown"] = thermo
        hour_resp["production"]["hydro"] = hydro
        hour_resp["production"]["wind"] = wind

        payload.append(hour_resp)

    return payload


def fetch_generation_forecast(zone_key='BO', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    now = arrow.now(tz=tz_bo)

    r = session or requests.session()

    # Define actual and previous day (for midnight data).
    formatted_date = now.format('YYYY-MM-DD')

    # initial path for url to request
    url_init = 'https://www.cndc.bo/gene/dat/gene.php?fechag={0}'

    # XSRF token for the initial request
    xsrf_token = extract_xsrf_token(r.get("https://www.cndc.bo/gene/index.php").text)

    resp = r.get(url_init.format(formatted_date), headers={
        "x-csrf-token": xsrf_token
    })

    hour_rows = json.loads(resp.text.replace('ï»¿', ''))["data"]
    payload = []

    for hour_row in hour_rows:
        [hour, forecast, _total, _thermo, _hydro, _wind, _unknown] = hour_row

        if hour == 24:
            timestamp = now.shift(days=1)
        else:
            timestamp = now

        zeroed = timestamp.replace(hour=hour-1, minute=0, second=0, microsecond=0)

        hour_resp = template_forecast_response(zone_key, zeroed.datetime, "cndc.bo")
        hour_resp["value"] = forecast

        payload.append(hour_resp)

    return payload

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print('fetch_production() ->')
    print(fetch_production())

    print('fetch_generation_forecast() ->')
    print(fetch_generation_forecast())
