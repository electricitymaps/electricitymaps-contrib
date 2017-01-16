import arrow
import pandas as pd
import requests

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
    endpoint = 'http://electricitymap.tmrow.co'
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
            print 'Fetching time %s..' % t
            o = fetch_production(country, t, delta)
            if not o: continue
            modes = o['production'].keys()
            p = pd.DataFrame(
                data={
                    'timestamp': pd.Timestamp(t.datetime),
                    'country': country,
                    'mode': modes,
                    'production': map(lambda k: o['production'][k], modes),
                })
            if df is not None: df = df.append(p)
            else: df = p
    return df

# get_exchange

def fetch_exchange(country_code, t):
    endpoint = 'http://electricitymap.tmrow.co'
    url = '%s/v1/state' % endpoint
    params = {
        'datetime': t.isoformat()
    }
    obj = r.get(url, params=params).json()
    if not obj['data']['countries'][country_code]: return
    return obj['data']['countries'][country_code]

def get_exchange(countries, start_date, end_date, delta):
    df = None
    time_span = date_range(start_date, end_date, delta)
    for country in countries:
        print 'Fetching country %s..' % country
        for t in time_span:
            print 'Fetching time %s..' % t
            o = fetch_exchange(country, t)
            p = pd.DataFrame({'country': country,
                              'timestamp': pd.Timestamp(t.datetime),
                              'country_exchange': o['exchange'].keys(),
                              'net_flow': o['exchange'].values()})
            if df is not None: df = df.append(p)
            else: df = p
    return df
