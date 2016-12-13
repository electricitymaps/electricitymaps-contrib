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
    print 'Fetching weather forecast of %s made at %s' % (horizon, origin)
    subprocess.check_call(
        ['wget', '-q', get_url(origin, horizon), '-O', TMP_FILENAME], shell=False)

    with pygrib.open(TMP_FILENAME) as f:
        wind_u = f.select(name='10 metre U wind component')[0]
        wind_v = f.select(name='10 metre V wind component')[0]
        solar  = f.select(name='Downward short-wave radiation flux', level=0)[0]
        latitudes, longitudes = wind_u.latlons()
        latitudes  = latitudes [::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        longitudes = longitudes[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        nx = np.unique(longitudes).size
        ny = np.unique(latitudes).size
        DSWRF = solar.values[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        UGRD = wind_u.values[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]
        VGRD = wind_v.values[::GRID_COMPRESSION_FACTOR, ::GRID_COMPRESSION_FACTOR]

        # Cleanup
        os.remove(TMP_FILENAME)

        # For backwards compatibility,
        # We're keeping the GRIB2JSON format for now
        obj = {
            'refTime': arrow.get(wind_u.analDate).datetime,
            'targetTime': arrow.get(wind_u.validDate).datetime,
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
                        'nx': nx,
                        'ny': ny,
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
                        'nx': nx,
                        'ny': ny,
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
                    'nx': nx,
                    'ny': ny,
                },
                'data': DSWRF.flatten().tolist()
            }
        }
        return obj
