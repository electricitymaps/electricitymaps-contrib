import arrow
import glob
import pymongo
import json, logging, os, schedule, time
import requests
import snappy

from bson.binary import Binary
from pymemcache.client.base import Client

from parsers import EE, FR, HU, RO
from parsers import ENTSOE
from parsers import PYISO
from parsers import weather
from migrate_db import migrate

INTERVAL_SECONDS = 60 * 5

# Set up error handling
import opbeat
from opbeat.handlers.logging import OpbeatHandler
if 'OPBEAT_SECRET' in os.environ:
    opbeat_client = opbeat.Client(
        app_id='c36849e44e',
        organization_id='093c53b0da9d43c4976cd0737fe0f2b1',
        secret_token=os.environ['OPBEAT_SECRET'])
else:
    opbeat_client = None
    print "No Opbeat Token found! Opbeat Error handling is inactive."

# Set up logging
ENV = os.environ.get('ENV', 'development').lower()
logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler()
logger.addHandler(stdout_handler)
if not ENV == 'development':
    logger.setLevel(logging.INFO)
    # Add opbeat
    if opbeat_client:
        opbeat_handler = OpbeatHandler(opbeat_client)
        opbeat_handler.setLevel(logging.WARN)
        logger.addHandler(opbeat_handler)
    # Add email
    from logging.handlers import SMTPHandler
    smtp_handler = SMTPHandler(
        mailhost=('smtp.mailgun.org', 587),
        fromaddr='Application Bug Reporter <noreply@mailgun.com>',
        toaddrs=['olivier.corradi@gmail.com'],
        subject='Electricity Map Feeder Error',
        credentials=(os.environ.get('MAILGUN_USER'), os.environ.get('MAILGUN_PASSWORD'))
    )
    smtp_handler.setLevel(logging.WARN)
    logger.addHandler(smtp_handler)
    # Add statsd
    logging.getLogger('statsd').addHandler(stdout_handler)
else:
    logger.setLevel(logging.DEBUG)

logger.info('Feeder is starting..')

# Define all production parsers
CONSUMPTION_PARSERS = {
    'AT': ENTSOE.fetch_consumption,
    'BE': ENTSOE.fetch_consumption,
    'BG': ENTSOE.fetch_consumption,
    'CH': ENTSOE.fetch_consumption,
    'CZ': ENTSOE.fetch_consumption,
    'DE': ENTSOE.fetch_consumption,
    'DK': ENTSOE.fetch_consumption,
    # 'EE': EE.fetch_consumption,
    'ES': ENTSOE.fetch_consumption,
    'FI': ENTSOE.fetch_consumption,
    # 'FR': FR.fetch_consumption,
    'GB': ENTSOE.fetch_consumption,
    'GR': ENTSOE.fetch_consumption,
    # 'HU': HU.fetch_consumption,
    'IE': ENTSOE.fetch_consumption,
    'IT': ENTSOE.fetch_consumption,
    'LT': ENTSOE.fetch_consumption,
    'LU': ENTSOE.fetch_consumption,
    'LV': ENTSOE.fetch_consumption,
    'NL': ENTSOE.fetch_consumption,
    'NO': ENTSOE.fetch_consumption,
    'PL': ENTSOE.fetch_consumption,
    'PT': ENTSOE.fetch_consumption,
    # 'RO': RO.fetch_consumption,
    'SE': ENTSOE.fetch_consumption,
    'SI': ENTSOE.fetch_consumption,
    'SK': ENTSOE.fetch_consumption,
}
PRODUCTION_PARSERS = {
    'AT': ENTSOE.fetch_production,
    'BE': ENTSOE.fetch_production,
    'BG': ENTSOE.fetch_production,
    'CH': ENTSOE.fetch_production,
    'CZ': ENTSOE.fetch_production,
    'DE': ENTSOE.fetch_production,
    'DK': ENTSOE.fetch_production,
    'EE': EE.fetch_production,
    'ES': ENTSOE.fetch_production,
    'FI': ENTSOE.fetch_production,
    'FR': FR.fetch_production,
    'GB': ENTSOE.fetch_production,
    'GR': ENTSOE.fetch_production,
    'HU': ENTSOE.fetch_production,
    'IE': ENTSOE.fetch_production,
    'IT': ENTSOE.fetch_production,
    'LT': ENTSOE.fetch_production,
    'LU': ENTSOE.fetch_production,
    'LV': ENTSOE.fetch_production,
    'NL': ENTSOE.fetch_production,
    'NO': ENTSOE.fetch_production,
    'PL': ENTSOE.fetch_production,
    'PT': ENTSOE.fetch_production,
    'RO': RO.fetch_production,
    'SE': ENTSOE.fetch_production,
    'SI': ENTSOE.fetch_production,
    'SK': ENTSOE.fetch_production,
}
# Keys are unique because both countries are sorted alphabetically
EXCHANGE_PARSERS = {
    # AL
    'AL->GR': ENTSOE.fetch_exchange,
    # AT
    'AT->CH': ENTSOE.fetch_exchange,
    'AT->CZ': ENTSOE.fetch_exchange,
    'AT->DE': ENTSOE.fetch_exchange,
    'AT->HU': ENTSOE.fetch_exchange,
    'AT->IT': ENTSOE.fetch_exchange,
    'AT->SI': ENTSOE.fetch_exchange,
    # BE
    'BE->FR': ENTSOE.fetch_exchange,
    'BE->NL': ENTSOE.fetch_exchange,
    # BG
    'BG->GR': ENTSOE.fetch_exchange,
    'BG->MK': ENTSOE.fetch_exchange,
    'BG->RO': RO.fetch_exchange,
    'BG->RS': ENTSOE.fetch_exchange,
    'BG->TR': ENTSOE.fetch_exchange,
    # BY
    'BY->LT': ENTSOE.fetch_exchange,
    # CH
    'CH->DE': ENTSOE.fetch_exchange,
    'CH->FR': ENTSOE.fetch_exchange,
    'CH->IT': ENTSOE.fetch_exchange,
    # CZ
    'CZ->SK': ENTSOE.fetch_exchange,
    'CZ->PL': ENTSOE.fetch_exchange,
    'CZ->DE': ENTSOE.fetch_exchange,
    # DE
    'DE->DK': ENTSOE.fetch_exchange,
    'DE->FR': ENTSOE.fetch_exchange,
    'DE->PL': ENTSOE.fetch_exchange,
    'DE->NL': ENTSOE.fetch_exchange,
    'DE->SE': ENTSOE.fetch_exchange,
    # DK
    'DK->NO': ENTSOE.fetch_exchange,
    'DK->SE': ENTSOE.fetch_exchange,
    # EE
    'EE->FI': ENTSOE.fetch_exchange,
    'EE->LV': ENTSOE.fetch_exchange,
    # ES
    'ES->FR': ENTSOE.fetch_exchange,
    'ES->PT': ENTSOE.fetch_exchange,
    # FI
    'FI->NO': ENTSOE.fetch_exchange,
    'FI->RU': ENTSOE.fetch_exchange,
    'FI->SE': ENTSOE.fetch_exchange,
    # FR
    'FR->GB': ENTSOE.fetch_exchange,
    'FR->IT': ENTSOE.fetch_exchange,
    # GB
    'GB->IE': ENTSOE.fetch_exchange,
    'GB->NL': ENTSOE.fetch_exchange,
    # GR
    'GR->IT': ENTSOE.fetch_exchange,
    'GR->MK': ENTSOE.fetch_exchange,
    'GR->TR': ENTSOE.fetch_exchange,
    # HR
    'HR->HU': ENTSOE.fetch_exchange,
    # HU
    'HU->RO': RO.fetch_exchange,
    'HU->RS': ENTSOE.fetch_exchange,
    'HU->SK': ENTSOE.fetch_exchange,
    # 'HU->UA': ENTSOE.fetch_exchange,
    # IT
    'IT->MT': ENTSOE.fetch_exchange,
    'IT->SI': ENTSOE.fetch_exchange,
    # LT
    'LT->LV': ENTSOE.fetch_exchange,
    'LT->PL': ENTSOE.fetch_exchange,
    'LT->RU': ENTSOE.fetch_exchange,
    'LT->SE': ENTSOE.fetch_exchange,
    # LV
    'LV->RU': ENTSOE.fetch_exchange,
    # MD
    'MD->RO': RO.fetch_exchange,
    # NL
    'NL->NO': ENTSOE.fetch_exchange,
    # NO
    'NO->SE': ENTSOE.fetch_exchange,
    # PL
    'PL->SE': ENTSOE.fetch_exchange,
    'PL->SK': ENTSOE.fetch_exchange,
    # RO
    'RO->RS': RO.fetch_exchange,
    'RO->UA': RO.fetch_exchange,
    # SK
    # 'SK->UA': ENTSOE.fetch_exchange,
}

# Set up stats
import statsd
statsd.init_statsd({
    'STATSD_HOST': os.environ.get('STATSD_HOST', 'localhost'),
    'STATSD_BUCKET_PREFIX': 'electricymap_feeder'
})

# Set up database
client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client['electricity']
col_consumption = db['consumption']
col_gfs = db['gfs']
col_production = db['production']
col_exchange = db['exchange']
# Set up indices
col_consumption.create_index([('datetime', -1), ('countryCode', 1)], unique=True)
col_gfs.create_index([('refTime', -1), ('targetTime', 1), ('key', 1)], unique=True)
col_gfs.create_index([('refTime', -1), ('targetTime', -1), ('key', 1)], unique=True)
col_production.create_index([('datetime', -1), ('countryCode', 1)], unique=True)
col_exchange.create_index([('datetime', -1), ('sortedCountryCodes', 1)], unique=True)

# Set up memcached
MEMCACHED_HOST = os.environ.get('MEMCACHED_HOST', None)
MEMCACHED_STATE_KEY = 'state'
if not MEMCACHED_HOST:
    logger.warn('MEMCACHED_HOST env variable was not found.. starting without cache!')
    cache = None
else: 
    cache = Client((MEMCACHED_HOST, 11211))

# Set up requests
session = requests.session()

def validate_consumption(obj, country_code):
    # Data quality check
    if obj['consumption'] is not None and obj['consumption'] < 0:
        raise ValueError('%s: consumption has negative value %s' % (country_code, obj['consumption']))

def validate_production(obj, country_code):
    if not 'datetime' in obj:
        raise Exception('datetime was not returned for %s' % country_code)
    if obj.get('countryCode', None) != country_code:
        raise Exception("Country codes %s and %s don't match" % (obj.get('countryCode', None), country_code))
    if arrow.get(obj['datetime']) > arrow.now():
        raise Exception("Data from %s can't be in the future" % country_code)
    if obj.get('production', {}).get('unknown', None) is None and \
        obj.get('production', {}).get('coal', None) is None and \
        country_code not in ['CH', 'NO']:
        raise Exception("Coal or unknown production value is required for %s" % (country_code))
    for k, v in obj['production'].iteritems():
        if v is None: continue
        if v < 0: raise ValueError('%s: key %s has negative value %s' % (country_code, k, v))

def db_upsert(col, obj, database_key):
    now = arrow.now().datetime
    query = { database_key: obj[database_key], 'datetime': obj['datetime'] }
    result = col.update_one(query, { '$set': obj }, upsert=True)
    if result.modified_count:
        logger.info('[%s] Updated %s @ %s' % (col.full_name, obj[database_key], obj['datetime']))
        col.update_one(query, { '$set': { 'modifiedAt': now } })
    elif result.matched_count:
        logger.debug('[%s] Already up to date: %s @ %s' % (col.full_name, obj[database_key], obj['datetime']))
    elif result.upserted_id:
        logger.info('[%s] Inserted %s @ %s' % (col.full_name, obj[database_key], obj['datetime']))
        col.update_one(query, { '$set': { 'createdAt': now } })
    else:
        raise Exception('Unknown database command result.')
    return result

def fetch_consumptions():
    for country_code, parser in CONSUMPTION_PARSERS.iteritems():
        try:
            with statsd.StatsdTimer('fetch_one_consumption'):
                obj = parser(country_code, session)
                if not obj: continue
                validate_consumption(obj, country_code)
                # Database insert
                result = db_upsert(col_consumption, obj, 'countryCode')
                if (result.modified_count or result.upserted_id) and cache: cache.delete(MEMCACHED_STATE_KEY)
        except:
            statsd.increment('fetch_one_consumption_error')
            logger.exception('Exception while fetching consumption of %s' % country_code)

def fetch_productions():
    for country_code, parser in PRODUCTION_PARSERS.iteritems():
        try:
            with statsd.StatsdTimer('fetch_one_production'):
                obj = parser(country_code, session)
                if not obj: continue
                validate_production(obj, country_code)
                # Database insert
                result = db_upsert(col_production, obj, 'countryCode')
                if (result.modified_count or result.upserted_id) and cache: cache.delete(MEMCACHED_STATE_KEY)
        except:
            statsd.increment('fetch_one_production_error')
            logger.exception('Exception while fetching production of %s' % country_code)

def fetch_exchanges():
    for k, parser in EXCHANGE_PARSERS.iteritems():
        try:
            with statsd.StatsdTimer('fetch_one_exchange'):
                country_code1, country_code2 = k.split('->')
                if sorted([country_code1, country_code2])[0] != country_code1:
                    raise Exception('Exchange key pair %s is not ordered alphabetically' % k)
                obj = parser(country_code1, country_code2, session)
                if not obj: continue
                if obj.get('sortedCountryCodes', None) != k:
                    raise Exception("Sorted country codes %s and %s don't match" % (obj.get('sortedCountryCodes', None), k))
                if not 'datetime' in obj:
                    raise Exception('datetime was not returned for %s' % k)
                if arrow.get(obj['datetime']) > arrow.now():
                    raise Exception("Data from %s can't be in the future" % k)
                # Database insert
                result = db_upsert(col_exchange, obj, 'sortedCountryCodes')
                if (result.modified_count or result.upserted_id) and cache: cache.delete(MEMCACHED_STATE_KEY)
        except:
            statsd.increment('fetch_one_exchange_error')
            logger.exception('Exception while fetching exchange of %s' % k)

def db_upsert_forecast(col, obj, database_key):
    now = arrow.now().datetime
    query = {
        database_key: obj[database_key],
        'refTime': obj['refTime'],
        'targetTime': obj['targetTime']
    }
    result = col.update_one(query, { '$set': obj }, upsert=True)
    delta_hours = int((obj['targetTime'] - obj['refTime']).total_seconds() / 3600.0)
    if result.modified_count:
        col.update_one(query, { '$set': { 'modifiedAt': now } })
        logger.info('[%s] Updated %s @ %s +%d' % (col.full_name, obj[database_key], obj['refTime'], delta_hours))
    elif result.matched_count:
        logger.debug('[%s] Already up to date: %s @ %s +%d' % (col.full_name, obj[database_key], obj['refTime'], delta_hours))
    elif result.upserted_id:
        col.update_one(query, { '$set': { 'createdAt': now } })
        logger.info('[%s] Inserted %s @ %s +%d' % (col.full_name, obj[database_key], obj['refTime'], delta_hours))
    else:
        raise Exception('Unknown database command result.')
    return result

def fetch_next_forecasts(now=None, lookahead=6, cached=False):
    if not now: now = arrow.utcnow()
    horizon = now.floor('hour')
    while (int(horizon.format('HH')) % weather.STEP_HORIZON) != 0:
        horizon = horizon.replace(hours=-1)
    # Warning: solar will not be available at horizon 0
    # so always do at least horizon 1
    origin = horizon.replace(hours=-1)
    while (int(origin.format('HH')) % weather.STEP_ORIGIN) != 0:
        origin = origin.replace(hours=-1)

    objs = []
    for i in range(lookahead):
        # Check if wind and solar are already in the database
        if cached:
            results = map(lambda d: d['key'], col_gfs.find({
                'refTime': origin.datetime,
                'targetTime': horizon.datetime
            }, projection={'key': 1}))
            delta_hours = int((horizon.datetime - origin.datetime).total_seconds() / 3600.0)
        if cached and set(results) == set(['wind', 'solar']):
            logger.debug('[%s] Already in database: %s @ %s +%d' % (col_gfs.full_name, ('wind', 'solar'), origin.datetime, delta_hours))
        else:
            objs.append(weather.fetch_forecast(origin, horizon))
        horizon = horizon.replace(hours=+weather.STEP_HORIZON)

    return objs

def fetch_weather():
    try:
        with statsd.StatsdTimer('fetch_weather'):
            objs = fetch_next_forecasts(cached=True)
            for obj in objs:
                wind = {
                    'refTime': obj['refTime'],
                    'targetTime': obj['targetTime'],
                    'data': Binary(snappy.compress(json.dumps(obj['wind']))),
                    'key': 'wind'
                }
                solar = {
                    'refTime': obj['refTime'],
                    'targetTime': obj['targetTime'],
                    'data': Binary(snappy.compress(json.dumps(obj['solar']))),
                    'key': 'solar'
                }
                db_upsert_forecast(col_gfs, wind, 'key')
                db_upsert_forecast(col_gfs, solar, 'key')
    except:
        statsd.increment('fetch_weather_error')
        logger.exception('fetch_weather()')

migrate(db, validate_production)

schedule.every(15).minutes.do(fetch_weather)
schedule.every(INTERVAL_SECONDS).seconds.do(fetch_consumptions)
schedule.every(INTERVAL_SECONDS).seconds.do(fetch_productions)
schedule.every(INTERVAL_SECONDS).seconds.do(fetch_exchanges)

fetch_weather()
fetch_consumptions()
fetch_productions()
fetch_exchanges()

while True:
    schedule.run_pending()
    time.sleep(10) # Only sleep for 10 seconds before checking again
