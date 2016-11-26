import arrow
import glob
import pymongo
import logging, os, schedule, time
import requests

from collections import defaultdict
from pymemcache.client.base import Client

from parsers import EE, FR, GB, HU, RO

from parsers import ENTSOE
from parsers import weather
from migrate_db import migrate

INTERVAL_SECONDS = 60 * 5

# Set up logging
ENV = os.environ.get('ENV', 'development').lower()
logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler()
logger.addHandler(stdout_handler)
if not ENV == 'development':
    logger.setLevel(logging.INFO)
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
    logging.getLogger('statsd').addHandler(stdout_handler)
else:
    logger.setLevel(logging.DEBUG)

logger.info('Feeder is starting..')

# Define all production parsers
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
    'GB': GB.fetch_production,
    'GR': ENTSOE.fetch_production,
    'HU': HU.fetch_production,
    'IE': ENTSOE.fetch_production,
    # 'IT': ENTSOE.fetch_production, # It is still missing coal for now (#72)
    'LT': ENTSOE.fetch_production,
    'LV': ENTSOE.fetch_production,
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
    # 'EE->LV': ENTSOE.fetch_exchange, # No data for now
    # ES
    'ES->FR': ENTSOE.fetch_exchange,
    'ES->PT': ENTSOE.fetch_exchange,
    # FI
    'FI->NO': ENTSOE.fetch_exchange,
    'FI->SE': ENTSOE.fetch_exchange,
    # FR
    'FR->GB': GB.fetch_exchange,
    'FR->IT': ENTSOE.fetch_exchange,
    # GB
    'GB->IE': GB.fetch_exchange,
    'GB->NL': GB.fetch_exchange,
    # GR
    'GR->IT': ENTSOE.fetch_exchange,
    'GR->MK': ENTSOE.fetch_exchange,
    # 'GR->TR': ENTSOE.fetch_exchange,
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
    'LT->SE': ENTSOE.fetch_exchange,
    # MD
    'MD->RO': RO.fetch_exchange,
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
col_production = db['production']
col_exchange = db['exchange']
# Set up indices
col_production.create_index([('datetime', -1), ('countryCode', 1)], unique=True)
col_exchange.create_index([('datetime', -1), ('sortedCountryCodes', 1)], unique=True)

# Set up memcached
MEMCACHED_HOST = os.environ.get('MEMCACHED_HOST', None)
MEMCACHED_KEY = 'state'
if not MEMCACHED_HOST:
    logger.warn('MEMCACHED_HOST env variable was not found.. starting without cache!')
    cache = None
else: cache = Client((MEMCACHED_HOST, 11211))

# Set up requests
session = requests.session()

REQUIRED_PRODUCTION_FIELDS = [
    'coal'
]
def validate_production(obj, country_code):
    if not 'datetime' in obj:
        raise Exception('datetime was not returned for %s' % country_code)
    if obj.get('countryCode', None) != country_code:
        raise Exception("Country codes %s and %s don't match" % (obj.get('countryCode', None), country_code))
    if arrow.get(obj['datetime']) > arrow.now():
        raise Exception("Data from %s can't be in the future" % country_code)
    for key in REQUIRED_PRODUCTION_FIELDS:
        if not key in obj.get('production', {}) or not obj['production'].get(key, None):
            raise Exception("Production %s is required for %s" % (key, country_code))

def db_upsert(col, obj, database_key):
    try:
        createdAt = arrow.now().datetime
        result = col.update_one(
            { database_key: obj[database_key], 'datetime': obj['datetime'] },
            { '$set': obj },
            upsert=True)
        if result.modified_count:
            logger.info('Updated %s @ %s' % (obj[database_key], obj['datetime']))
        elif result.matched_count:
            logger.debug('Already up to date: %s @ %s' % (obj[database_key], obj['datetime']))
        elif result.upserted_id:
            logger.info('Inserted %s @ %s' % (obj[database_key], obj['datetime']))
        else:
            raise Exception('Unknown database command result.')
        # Only update createdAt time if upsert happened
        if result.modified_count or result.upserted_id:
            col.update_one(
                { database_key: obj[database_key], 'datetime': obj['datetime'] },
                { '$set': { 'createdAt': createdAt } })
        return result
    except pymongo.errors.DuplicateKeyError:
        # (datetime, countryCode) does already exist. Don't raise.
        # Note: with this design, the oldest record stays.
        logger.info('Successfully fetched %s @ %s but did not insert into the db because it already existed' % (obj[database_key], obj['datetime']))

def fetch_productions():
    for country_code, parser in PRODUCTION_PARSERS.iteritems():
        try:
            with statsd.StatsdTimer('fetch_one_production'):
                obj = parser(country_code, session)
                if not obj: continue
                validate_production(obj, country_code)
                # Data quality check
                for k, v in obj['production'].iteritems():
                    if v is None: continue
                    if v < 0: raise ValueError('%s: key %s has negative value %s' % (country_code, k, v))
                # Database insert
                result = db_upsert(col_production, obj, 'countryCode')
                if (result.modified_count or result.upserted_id) and cache: cache.delete(MEMCACHED_KEY)
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
                if (result.modified_count or result.upserted_id) and cache: cache.delete(MEMCACHED_KEY)
        except:
            statsd.increment('fetch_one_exchange_error')
            logger.exception('Exception while fetching exchange of %s' % k)

def fetch_weather():
    try:
        with statsd.StatsdTimer('fetch_weather'): weather.fetch_weather()
    except:
        statsd.increment('fetch_weather_error')
        logger.exception('fetch_weather()')

migrate(db, validate_production)

schedule.every(INTERVAL_SECONDS).seconds.do(fetch_productions)
schedule.every(INTERVAL_SECONDS).seconds.do(fetch_exchanges)
schedule.every(15).minutes.do(fetch_weather)

fetch_productions()
fetch_exchanges()
fetch_weather()

while True:
    schedule.run_pending()
    time.sleep(10) # Only sleep for 10 seconds before checking again
