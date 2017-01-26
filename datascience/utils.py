import arrow
import pandas as pd
import requests

endpoint = 'http://www.electricitymap.org'
r = requests.session()

def date_range(start_date, end_date, delta):
    start, end = [
        arrow.get(start_date),
        arrow.get(end_date)
    ]
    if end < start: raise Exception('End date can\' be before start date')
    time_span = [start]
    while True:
        t = time_span[-1].replace(minutes=+delta)
        if t > end: break
        time_span.append(t)
    return time_span

# get_production

def fetch_production(country_code, t, delta):
    url = '%s/v1/production' % endpoint
    params = {
        'countryCode': country_code,
        'datetime': t.isoformat()
    }
    obj = r.get(url, params=params).json()
    if not obj: return
    return obj if (t - arrow.get(obj['datetime'])).total_seconds() < delta * 60.0 else None

def get_production(countries, start_date, end_date, delta):
    df = None
    time_span = date_range(start_date, end_date, delta)
    for country in countries:
        print 'Fetching country %s..' % country
        for t in time_span:
            o = fetch_production(country, t, delta)
            if not o: continue
            modes = o['production'].keys()
            p = pd.DataFrame(
                data={
                    'timestamp': pd.Timestamp(arrow.get(o['datetime']).datetime),
                    'country': country,
                    'mode': modes,
                    'production': map(lambda k: o['production'][k], modes),
                })
            if df is not None: df = df.append(p)
            else: df = p
    return df

# get_exchange

def fetch_exchange(country_code, t):
    url = '%s/v1/exchanges' % endpoint
    params = {
        'datetime': t.isoformat(),
        'countryCode': country_code
    }
    obj = r.get(url, params=params).json()
    return obj['data']

def get_exchange(countries, start_date, end_date, delta):
    df = None
    time_span = date_range(start_date, end_date, delta)
    for country_code in countries:
        print 'Fetching country %s..' % country_code
        for t in time_span:
            o = fetch_exchange(country_code, t)
            if not o: continue
            country_exchanges = o.values()
            # Make sure `from` is always `country_code`
            country_tos = []
            net_flows = []
            for item in country_exchanges:
                sorted_country_codes = item['sortedCountryCodes'].split('->')
                if sorted_country_codes[0] == country_code:
                    country_tos.append(sorted_country_codes[1])
                    net_flows.append(item['netFlow'])
                else:
                    country_tos.append(sorted_country_codes[0])
                    net_flows.append(-1 * item['netFlow'])
            timestamps = map(lambda x: pd.Timestamp(arrow.get(x['datetime']).datetime),
                country_exchanges)
            p = pd.DataFrame({'country_from': country_code,
                              'timestamp': timestamps,
                              'country_to': country_tos,
                              'net_flow': net_flows})
            if df is not None: df = df.append(p)
            else: df = p
    return df
