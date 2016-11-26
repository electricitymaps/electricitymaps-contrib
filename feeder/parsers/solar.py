import arrow, gzip, json, os, subprocess
import pygrib

BASE = '00'
MULTIPLE_ORIGIN = 6
MULTIPLE_HORIZON = 6
SW = [-48.66, 28.17]
NE = [37.45, 67.71]

def get_url(origin, horizon):
    return 'http://nomads.ncep.noaa.gov/cgi-bin/filter_cfs_flx.pl?' + \
        'file=flxf%s.01.%s.grb2' % (horizon.format('YYYYMMDDHH'), origin.format('YYYYMMDDHH')) + \
        '&lev_surface=on&var_DLWRF=on&var_DSWRF=on&leftlon=%d&rightlon=%d&toplat=%d&bottomlat=%d' % (180 + SW[0], 180 + NE[0], NE[1], SW[1]) + \
        '&dir=%%2Fcfs.%s%%2F%s%%2F6hrly_grib_01' % (origin.format('YYYYMMDD'), origin.format('HH'))

def fetch_forecast(origin, horizon):
    isBest = False
    for i in range(3):
        if i > 0: print 'Trying with an earlier origin..'
        try:
            print 'Fetching forecast of %s made at %s' % (horizon, origin)
            subprocess.check_call(['wget', '-nv', get_url(origin, horizon), '-O', 'solar.grb2'], shell=False)
            if i == 0: isBest = True
            print 'Success!'
            break
        except subprocess.CalledProcessError:
            if i == 2: raise Exception('Couldn\' find a forecast')
            origin = origin.replace(hours=-MULTIPLE_ORIGIN)
            
    with pygrib.open('solar.grb2') as f:
        #print f.select(name='Downward long-wave radiation flux', level=0)
        grb_LW = f.select(name='Downward long-wave radiation flux', level=0)[0]
        grb_SW = f.select(name='Downward short-wave radiation flux', level=0)[0]
        return ({
            'lonlats': [grb_SW['longitudes'].tolist(), grb_SW['latitudes'].tolist()],
            'DLWRF': grb_LW['values'].tolist(),
            'DSWRF': grb_SW['values'].tolist(),
            'horizon': horizon.isoformat(),
            'date': origin.isoformat()
        }, isBest)

def fetch_solar(session=None, now=None, compress=True, useCache=True):
    if not session: pass
    if not now: now = arrow.utcnow()
    now = now.to('utc')

    horizon = now.floor('hour')
    while (int(horizon.format('HH')) % MULTIPLE_HORIZON) != 0:
        horizon = horizon.replace(hours=-1)
    origin = horizon

    # Read cache for horizon
    if (useCache):
        cache_filename = 'data/solarcache_%s.json.gz' % horizon.timestamp
        if os.path.exists(cache_filename):
            with gzip.open(cache_filename, 'r') as f:
                return json.load(f)

    obj_before, beforeIsBestForecast = fetch_forecast(origin, horizon)
    obj_after, afterIsBestForecast = fetch_forecast(origin, horizon.replace(hours=+MULTIPLE_HORIZON))
    obj = {
        'forecasts': [obj_before, obj_after]
    }

    if compress:
        with gzip.open('data/solar.json.gz', 'w') as f:
            json.dump(obj, f)
    if useCache and beforeIsBestForecast and afterIsBestForecast:
        cache_filename = 'data/solarcache_%s.json.gz' % horizon.timestamp
        with gzip.open(cache_filename, 'w') as f:
            json.dump(obj, f)
    print 'Done'
    return obj

if __name__ == '__main__':
    fetch_solar()
    
