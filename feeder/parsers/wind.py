import arrow, gzip, json, os, pygrib, subprocess

BASE = '00'
MULTIPLE_ORIGIN = 6
MULTIPLE_HORIZON = 3
SW = [-48.66, 28.17]
NE = [37.45, 67.71]

def get_url(origin, horizon):
    delta_hours = int(((horizon - origin).total_seconds()) / 3600.0)
    return 'http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl?' + \
        'dir=%%2Fgfs.%s' % (origin.format('YYYYMMDDHH')) + \
        '&file=gfs.t%sz.pgrb2.1p00.f0%02d' % (origin.format('HH'), delta_hours) + \
        '&lev_10_m_above_ground=on&var_UGRD=on&var_VGRD=on&leftlon=%d&rightlon=%d&toplat=%d&bottomlat=%d' % (180 + SW[0], 180 + NE[0], NE[1], SW[1])

def fetch_forecast(origin, horizon):
    try:
        print 'Fetching forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call(
            ['wget', '-nv', get_url(origin, horizon), '-O', 'wind.grb2'], shell=False)
        return ('wind.grb2', True) # (filename, isBest)
    except subprocess.CalledProcessError:
        origin = origin.replace(hours=-MULTIPLE_ORIGIN)
        print 'Trying instead to fetch forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call(
            ['wget', '-nv', get_url(origin, horizon), '-O', 'wind.grb2'], shell=False)
        return ('wind.grb2', False) # (filename, isBest)


    # with pygrib.open('wind.grb2') as f:
    #     U_cmp = f.select(name='10 metre U wind component')[0]
    #     V_cmp = f.select(name='10 metre V wind component')[0]
    #     return {
    #         'lonlats': [U_cmp['longitudes'].tolist(), U_cmp['latitudes'].tolist()],
    #         'U_cmp': U_cmp['values'].tolist(),
    #         'V_cmp': V_cmp['values'].tolist(),
    #         'horizon': horizon.isoformat(),
    #         'date': origin.isoformat()
    #     }

def fetch_wind(session=None, now=None, compress=True, useCache=True):
    if not session: pass
    if not now: now = arrow.utcnow()
    # Fetch both a forecast before and after the current time
    horizon = now.floor('hour')
    while (int(horizon.format('HH')) % MULTIPLE_HORIZON) != 0:
        horizon = horizon.replace(hours=-1)
    origin = horizon
    while (int(origin.format('HH')) % MULTIPLE_ORIGIN) != 0:
        origin = origin.replace(hours=-1)

    # Read cache for horizon
    if (useCache):
        cache_filename = 'data/windcache_%s.json.gz' % horizon.timestamp
        if os.path.exists(cache_filename):
            with gzip.open(cache_filename, 'r') as f:
                return json.load(f)

    _, beforeIsBestForecast = fetch_forecast(origin, horizon)
    subprocess.check_call([
        'java',
        '-Xmx512M',
        '-jar', 'grib2json/grib2json-0.8.0-SNAPSHOT/lib/grib2json-0.8.0-SNAPSHOT.jar',
        '-d', '-n', '-c', '-o',
        'data/wind_before.json', 'wind.grb2'], shell=False)


    # Fetch the forecast after
    _, afterIsBestForecast = fetch_forecast(origin, horizon.replace(hours=+MULTIPLE_HORIZON))
    subprocess.check_call([
        'java',
        '-Xmx512M',
        '-jar', 'grib2json/grib2json-0.8.0-SNAPSHOT/lib/grib2json-0.8.0-SNAPSHOT.jar',
        '-d', '-n', '-c', '-o',
        'data/wind_after.json', 'wind.grb2'], shell=False)

    # Compress to json.gz
    with open('data/wind_before.json') as f_before, \
        open('data/wind_after.json') as f_after:
        obj = {
            'forecasts': [json.load(f_before), json.load(f_after)]
        }
        if compress:
            with gzip.open('data/wind.json.gz', 'w') as f_out:
                json.dump(obj, f_out)
        if useCache and beforeIsBestForecast and afterIsBestForecast:
            cache_filename = 'data/windcache_%s.json.gz' % horizon.timestamp
            with gzip.open(cache_filename, 'w') as f:
                json.dump(obj, f)
        print 'Done'
        return obj

if __name__ == '__main__':
    fetch_wind()
    
