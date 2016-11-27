import arrow, gzip, json, os, subprocess
import pygrib
import numpy as np

UTC_BASE = '00'
STEP_ORIGIN  = 6 # hours
STEP_HORIZON = 1 # hours
GRID_DELTA = 0.25 # degrees
GRID_COMPRESSION_FACTOR = 4 # will multiply delta by this factor
SW = [-48.66, 28.17]
NE = [37.45, 67.71]

TMP_FILENAME = 'tmp.grb2'

def get_url(origin, horizon):
    delta_hours = int(((horizon - origin).total_seconds()) / 3600.0)
    return 'http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p%d_1hr.pl?' % int(GRID_DELTA * 100) + \
        'dir=%%2Fgfs.%s' % (origin.format('YYYYMMDDHH')) + \
        '&file=gfs.t%sz.pgrb2.0p%d.f0%02d' % (origin.format('HH'), int(GRID_DELTA * 100), delta_hours) + \
        '&lev_10_m_above_ground=on&lev_surface=on' + \
        '&var_UGRD=on&var_VGRD=on&var_DSWRF=on' + \
        '&leftlon=%d&rightlon=%d&toplat=%d&bottomlat=%d' % (180 + SW[0], 180 + NE[0], NE[1], SW[1])

def fetch_forecast(origin, horizon):
    isBest = False
    try:
        print 'Fetching weather forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call(
            ['wget', '-q', get_url(origin, horizon), '-O', TMP_FILENAME], shell=False)
        isBest = True
    except subprocess.CalledProcessError:
        origin = origin.replace(hours=-STEP_ORIGIN)
        print 'Trying instead to fetch weather forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call(
            ['wget', '-q', get_url(origin, horizon), '-O', TMP_FILENAME], shell=False)

    with pygrib.open(TMP_FILENAME) as f:
        wind_u = f.select(name='10 metre U wind component')[0]
        wind_v = f.select(name='10 metre V wind component')[0]
        solar  = f.select(name='Downward short-wave radiation flux', level=0)[0]
        latitudes, longitudes = wind_u.latlons()
        latitudes  = latitudes [::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        longitudes = longitudes[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        DSWRF = solar.values[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        UGRD = wind_u.values[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        VGRD = wind_v.values[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]

        # Cleanup
        os.remove(TMP_FILENAME)

        # For backwards compatibility,
        # We're keeping the GRIB2JSON format for now
        obj = {
            'forecastTime': arrow.get(wind_u.analDate).isoformat(),
            'targetTime': arrow.get(wind_u.validDate).isoformat(),
            'wind': [
                {
                    'header': {
                        'refTime': arrow.get(wind_u.analDate).to('utc').isoformat(),
                        'forecastTime': int(
                            (arrow.get(wind_u.validDate) - arrow.get(wind_u.analDate)).total_seconds() / 3600.0),
                        'lo1': longitudes[0][0],
                        'la1': latitudes[0][0],
                        'dx': GRID_DELTA * GRID_COMPRESSION_FACTOR,
                        'dy': GRID_DELTA * GRID_COMPRESSION_FACTOR,
                        'nx': np.unique(longitudes).size,
                        'ny': np.unique(latitudes).size,
                        'parameterCategory': 2,
                        'parameterNumber': 2
                    },
                    'data': UGRD.flatten().tolist()
                },
                {
                    'header': {
                        'refTime': arrow.get(wind_v.analDate).to('utc').isoformat(),
                        'forecastTime': int(
                            (arrow.get(wind_v.validDate) - arrow.get(wind_v.analDate)).total_seconds() / 3600.0),
                        'lo1': longitudes[0][0],
                        'la1': latitudes[0][0],
                        'dx': GRID_DELTA * GRID_COMPRESSION_FACTOR,
                        'dy': GRID_DELTA * GRID_COMPRESSION_FACTOR,
                        'nx': longitudes.size,
                        'ny': latitudes.size,
                        'parameterCategory': 2,
                        'parameterNumber': 3
                    },
                    'data': VGRD.flatten().tolist()
                }
            ],
            'solar': {
                'header': {
                    'refTime': arrow.get(solar.analDate).to('utc').isoformat(),
                    'forecastTime': int(
                        (arrow.get(solar.validDate) - arrow.get(solar.analDate)).total_seconds() / 3600.0),
                    'lo1': longitudes[0][0],
                    'la1': latitudes[0][0],
                    'dx': GRID_DELTA * GRID_COMPRESSION_FACTOR,
                    'dy': GRID_DELTA * GRID_COMPRESSION_FACTOR,
                    'nx': longitudes.size,
                    'ny': latitudes.size,
                },
                'data': DSWRF.flatten().tolist()
            }
        }
        return (obj, isBest)

def fetch_weather(now=None, compress=True, useCache=False):
    if not now: now = arrow.utcnow()
    horizon = now.floor('hour')
    while (int(horizon.format('HH')) % STEP_HORIZON) != 0:
        horizon = horizon.replace(hours=-1)
    # Warning: solar will not be available at horizon 0
    # so always do at least horizon 1
    origin = horizon.replace(hours=-1)
    while (int(origin.format('HH')) % STEP_ORIGIN) != 0:
        origin = origin.replace(hours=-1)

    # Read cache for horizon
    if (useCache):
        cache_filename = 'data/weathercache_%s.json.gz' % horizon.timestamp
        if os.path.exists(cache_filename):
            with gzip.open(cache_filename, 'r') as f:
                return json.load(f)

    # Fetch both a forecast before and after the current time
    obj_before, beforeIsBestForecast = fetch_forecast(origin, horizon)
    obj_after, afterIsBestForecast = fetch_forecast(origin, horizon.replace(hours=+STEP_HORIZON))

    obj = {
        'forecasts': [obj_before, obj_after]
    }

    # Backwards compatibility: dump to wind files
    if compress:
        with gzip.open('data/wind.json.gz', 'w') as f_out:
            print 'Writing gzipped json..'
            json.dump({
                'forecasts': [obj_before['wind'], obj_after['wind']]
            }, f_out)
    if useCache and beforeIsBestForecast and afterIsBestForecast:
        cache_filename = 'data/weathercache_%s.json.gz' % horizon.timestamp
        with gzip.open(cache_filename, 'w') as f:
            json.dump(obj, f)

    return obj
    print 'Done'

if __name__ == '__main__':
    fetch_weather()
