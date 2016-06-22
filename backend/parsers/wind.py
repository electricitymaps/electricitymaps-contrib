import arrow, json, pygrib, subprocess

BASE = '00'
MULTIPLE = 6
SW = [-48.66, 28.17]
NE = [37.45, 67.71]

def get_url(origin, horizon):
    delta_hours = int(((horizon - origin).total_seconds()) / 3600.0)
    return 'http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p50.pl?' + \
        'file=gfs.t%sz.pgrb2full.0p50.f0%02d' % (origin.format('HH'), delta_hours) + \
        '&lev_10_m_above_ground=on&var_UGRD=on&var_VGRD=on&leftlon=%d&rightlon=%d&toplat=%d&bottomlat=%d' % (180 + SW[0], 180 + NE[0], NE[1], SW[1]) + \
        '&dir=%%2Fgfs.%s' % (origin.format('YYYYMMDDHH'))

def fetch_forecast(origin, horizon):
    try:
        print 'Fetching forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call('wget "%s" -O wind.grb2' % (get_url(origin, horizon)), shell=True)
    except subprocess.CalledProcessError:
        origin = origin.replace(hours=-MULTIPLE)
        print 'Fetching forecast of %s made at %s' % (horizon, origin)
        subprocess.check_call('wget "%s" -O wind.grb2' % (get_url(origin, horizon)), shell=True)

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

def fetch_wind():
    horizon = arrow.utcnow().floor('hour')
    while (int(horizon.format('HH')) % MULTIPLE) != 0:
        horizon = horizon.replace(hours=-1)
    origin = horizon

    obj_before = fetch_forecast(origin, horizon)
    subprocess.check_call('JAVA_HOME="`/usr/libexec/java_home -v 1.8`" java -Xmx512M -jar grib2json/target/grib2json-0.8.0-SNAPSHOT/lib/grib2json-0.8.0-SNAPSHOT.jar ' + \
        '-d -n -o data/wind.json wind.grb2', shell=True)
    # obj_after = fetch_forecast(origin, horizon.replace(hours=+MULTIPLE))
    # obj = {
    #     'forecasts': [obj_before, obj_after]
    # }

    # with open('data/wind.json', 'w') as f:
    #     json.dump(obj, f)

if __name__ == '__main__':
    fetch_wind()
    
