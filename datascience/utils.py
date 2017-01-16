import arrow
import pandas as pd
import requests

r = requests.session()

def date_range(start_date, end_date, delta):
    start, end = [
        arrow.get(start_date),
        arrow.get(end_date)
    ]
    time_span = [start]
    while True:
        t = time_span[-1].replace(minutes=+delta)
        if t > end: break
        time_span.append(t)
    return time_span

def fetch_production(country_code, t, delta):
    endpoint = 'http://electricitymap.tmrow.co'
    url = '%s/v1/production' % endpoint
    params = {
        'countryCode': country_code,
        'datetime': t.to('utc').isoformat()
    }
    obj = r.get(url, params=params).json()
    if not obj: return
    return obj if (t - arrow.get(obj['datetime'])).total_seconds() < delta * 60.0 else None

def get_production(countries, start_date, end_date, delta):
    df = pd.DataFrame(columns=['country','timestamp','sources','production'])
    time_span = date_range(start_date, end_date,delta)
    for country in countries:
        print 'Fetching country %s..' % country
        for t in time_span:
            print 'Fetching time %s..' % t
            o = fetch_production(country, t, delta)
            p = pd.DataFrame({'country': country,
                              'timestamp': t ,
                              'sources': o['production'].keys(),
                              'production': o['production'].values()})
            df = df.append(p)
    return df
