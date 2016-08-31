import arrow, gzip, json, pygrib, subprocess

BASE = '00'
MULTIPLE = 6
SW = [-48.66, 28.17]
NE = [37.45, 67.71]

def get_url(origin, horizon):
    return 'http://nomads.ncep.noaa.gov/cgi-bin/filter_cfs_flx.pl?' + \
        'file=flxf%s.01.%s.grb2' % (horizon.format('YYYYMMDDHH'), origin.format('YYYYMMDDHH')) + \
        '&lev_surface=on&var_DLWRF=on&var_DSWRF=on&leftlon=%d&rightlon=%d&toplat=%d&bottomlat=%d' % (180 + SW[0], 180 + NE[0], NE[1], SW[1]) + \
        '&dir=%%2Fcfs.%s%%2F%s%%2F6hrly_grib_01' % (origin.format('YYYYMMDD'), origin.format('HH'))

def fetch_forecast(origin, horizon):
    try:
        print 'Fetching forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call(['wget', '-nv', get_url(origin, horizon), '-O solar.grb2'], shell=False)
    except subprocess.CalledProcessError:
        origin = origin.replace(hours=-MULTIPLE)
        print 'Trying instead to fetch forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call(['wget', '-nv', get_url(origin, horizon), '-O solar.grb2'], shell=False)

    with pygrib.open('solar.grb2') as f:
        #print f.select(name='Downward long-wave radiation flux', level=0)
        grb_LW = f.select(name='Downward long-wave radiation flux', level=0)[-1]
        grb_SW = f.select(name='Downward short-wave radiation flux', level=0)[-1]
        return {
            'lonlats': [grb_LW['longitudes'].tolist(), grb_LW['latitudes'].tolist()],
            'DLWRF': grb_LW['values'].tolist(),
            'DSWRF': grb_SW['values'].tolist(),
            'horizon': horizon.isoformat(),
            'date': origin.isoformat()
        }

def fetch_solar():
    horizon = arrow.utcnow().floor('hour')
    while (int(horizon.format('HH')) % MULTIPLE) != 0:
        horizon = horizon.replace(hours=-1)
    origin = horizon

    obj_before = fetch_forecast(origin, horizon)
    obj_after = fetch_forecast(origin, horizon.replace(hours=+MULTIPLE))
    obj = {
        'forecasts': [obj_before, obj_after]
    }

    with gzip.open('data/solar.json.gz', 'w') as f:
        json.dump(obj, f)
    print 'Done'

if __name__ == '__main__':
    fetch_solar()
    
