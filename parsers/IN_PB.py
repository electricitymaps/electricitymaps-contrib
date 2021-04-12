
from collections import defaultdict

import arrow
import requests

GENERATION_URL = "http://www.pstcl.org:9091/scadadata/pbGenData2"

GENERATION_MAPPING = {"totalHydro": "hydro",
                      "totalThermal": "coal",
                      "totalIpp": "coal",
                      "resSolar": "solar",
                      "resNonSolar": "biomass"}


def calculate_average_timestamp(timestamps):
    """Takes a list of string timestamps and returns the average as an arrow object."""
    arrow_timestamps = [arrow.get(ts, tzinfo="Asia/Kolkata") for ts in timestamps if ts is not None]
    unix_timestamps = [ts.timestamp for ts in arrow_timestamps]
    average_timestamp = sum(unix_timestamps)/len(unix_timestamps)
    arr_average_timestamp = arrow.get(average_timestamp).to("Asia/Kolkata")

    return arr_average_timestamp


def fetch_production(zone_key='IN-PB', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
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
    if target_datetime:
        raise NotImplementedError('The IN-PB production parser is not yet able to parse past dates')

    s = session or requests.Session()
    req = s.get(GENERATION_URL)

    raw_data = req.json()

    timestamps = []
    valid_data = []
    for key in raw_data.keys():
        if key in GENERATION_MAPPING.keys():
            valid_data.append((key, raw_data[key]["value"]))
            timestamps.append(raw_data[key]["chartDate"])

    arr_dt = calculate_average_timestamp(timestamps)

    mapped_generation = [(GENERATION_MAPPING.get(gen_type), val) for (gen_type, val) in valid_data]
    production = defaultdict(lambda: 0.0)

    # Sum values for duplicate keys.
    for key, val in mapped_generation:
        production[key] += val

    data = {"zoneKey": zone_key,
            "datetime": arr_dt.datetime,
            "production": dict(production),
            "storage": {},
            "source": "punjasldc.org"}

    return data


def fetch_consumption(zone_key='IN-PB', session=None, target_datetime=None, logger=None):
    """
    Requests the last known consumption (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': 2832.5,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('The IN-PB consumption parser is not yet able to parse past dates')

    s = session or requests.Session()
    req = s.get(GENERATION_URL)
    raw_data = req.json()

    consumption = float(raw_data["grossGeneration"]["value"])

    data = {
        'zoneKey': zone_key,
        'datetime': arrow.now("Asia/Kolkata").datetime,
        'consumption': consumption,
        'source': "punjasldc.org"
    }

    return data


if __name__ == '__main__':
    print(fetch_production('IN-PB'))
    print(fetch_consumption('IN-PB'))
