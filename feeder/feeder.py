import arrow
import glob
import pymongo
import logging, os, schedule, time
import requests

from collections import defaultdict
from pymemcache.client.base import Client

from parsers.ENTSOE import fetch_ENTSOE
from parsers.solar import fetch_solar
from parsers.wind import fetch_wind

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

# Import all country parsers
def import_country(country_code):
    return getattr(
        __import__('parsers.%s' % country_code, globals(), locals(), ['fetch_%s' % country_code]),
        'fetch_%s' % country_code)
country_codes = map(lambda s: s[len('parsers/'):len('parsers/')+2], glob.glob('parsers/??.py'))
custom_parsers = map(import_country, country_codes)

# Define ENTSOE parsers
ENTSOE_DOMAINS = {
    'AT': '10YAT-APG------L',
    'BE': '10YBE----------2',
    'CH': '10YCH-SWISSGRIDZ',
    'CZ': '10YCZ-CEPS-----N',
    'DE': '10Y1001A1001A83F',
    'DK': '10Y1001A1001A65H',
    'ES': '10YES-REE------0',
    'FI': '10YFI-1--------U',
    'FR': '10YFR-RTE------C',
    'GR': '10YGR-HTSO-----Y',
    'IE': '10YIE-1001A00010',
    'IT': '10YIT-GRTN-----B',
    'LT': '10YLT-1001A0008Q',
    'LV': '10YLV-1001A00074',
    'NO': '10YNO-0--------C',
    'PL': '10YPL-AREA-----S',
    'PT': '10YPT-REN------W',
    'SE': '10YSE-1--------K',
    'SI': '10YSI-ELES-----O',
    'SK': '10YSK-SEPS-----K',
}
ENTSOE_NEIGHBOR_PAIRS = [
    # AT
    ('AT', 'CH'),
    ('AT', 'CZ'),
    ('AT', 'DE'),
    ('AT', 'IT'),
    ('AT', 'SI'),
    ('AT', 'SK'),
    # BE
    ('BE', 'DE'),
    ('BE', 'FR'),
    ('BE', 'NL'),
    # CH
    ('CH', 'DE'),
    ('CH', 'FR'),
    # CZ
    ('CZ', 'SK'),
    ('CZ', 'PL'),
    ('CZ', 'DE'),
    # DE
    ('DE', 'PL'),
    # DK
    ('DE', 'DK'),
    ('SE', 'DK'),
    ('DK', 'NO'),
    # GB
    ('GB', 'FR'),
    ('IE', 'GB'),
    ('NL', 'GB'),
    # FI
    ('FI', 'SE'),
    # FR
    ('FR', 'ES'),
    ('FR', 'DE'),
    ('FR', 'IT'),
    # HU
    ('HU', 'SK'),
    # IT
    ('IT', 'SI'),
    # LT
    ('LT', 'PL'),
    ('LT', 'LV'),
    # PL
    ('PL', 'SK'),
    # NO
    ('NO', 'SE'),
    # RO
    ('RO', 'HU'),
    ('RO', 'UA'),
    ('RO', 'MD'),
    ('RO', 'BG'),
    ('RO', 'RS'),
    # HU
    ('HU', 'SK'),
    ('HU', 'UA'),
    ('HU', 'RS'),
    ('HU', 'HR'),
    ('HU', 'AT'),
    # PT
    ('PT', 'ES'),
    # SK
    ('SK', 'UA'),
]
ENTSOE_NEIGHBORING_DOMAINS = defaultdict(lambda: {})
for o, d in ENTSOE_NEIGHBOR_PAIRS:
    if d in ENTSOE_DOMAINS: ENTSOE_NEIGHBORING_DOMAINS[o][d] = ENTSOE_DOMAINS[d]
    if o in ENTSOE_DOMAINS: ENTSOE_NEIGHBORING_DOMAINS[d][o] = ENTSOE_DOMAINS[o]

# Set up stats
import statsd
statsd.init_statsd({
    'STATSD_HOST': os.environ.get('STATSD_HOST', 'localhost'),
    'STATSD_BUCKET_PREFIX': 'electricymap_feeder'
})

# Set up database
client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client['electricity']
col = db['realtime']

# Set up memcached
MEMCACHED_HOST = os.environ.get('MEMCACHED_HOST', None)
if not MEMCACHED_HOST:
    logger.warn('MEMCACHED_HOST env variable was not found.. starting without cache!')
    cache = None
else: cache = Client((MEMCACHED_HOST, 11211))

# Set up requests
session = requests.session()

def execute_parser(parser):
    try:
        with statsd.StatsdTimer('fetch_one_country'):
            obj = parser(session)
            if not 'datetime' in obj:
                raise Exception('datetime was not returned from %s' % parser)
            if not 'countryCode' in obj:
                raise Exception('countryCode was not returned from %s' % parser)
            if arrow.get(obj['datetime']) > arrow.now():
                print 'future:', obj['datetime'], 'now', arrow.now()
                raise Exception("Data from %s can't be in the future" % obj['countryCode'])
            try:
                col.insert_one(obj)
                logger.info('Inserted %s @ %s into the db' % (obj.get('countryCode'), obj.get('datetime')))
                logger.debug(obj)
                if cache: cache.delete('production')
            except pymongo.errors.DuplicateKeyError:
                # (datetime, countryCode) does already exist. Don't raise.
                # Note: with this design, the oldest record stays.
                logger.info('Successfully fetched %s @ %s but did not insert into the db because it already existed' % (obj.get('countryCode'), obj.get('datetime')))
                pass
    except:
        statsd.increment('fetch_one_country_error')
        logger.exception('Exception while fetching one country')

def fetch_entsoe_countries():
    for countryCode, domain in ENTSOE_DOMAINS.iteritems():
        # Warning: lambda looks up the variable name at execution,
        # so this can't be parallelised in this state
        parser = lambda session: fetch_ENTSOE(
            domain,
            ENTSOE_NEIGHBORING_DOMAINS.get(countryCode, {}),
            countryCode,
            session)
        execute_parser(parser)

def fetch_custom_countries():
    for parser in custom_parsers: execute_parser(parser)

def fetch_weather():
    try:
        with statsd.StatsdTimer('fetch_wind'): fetch_wind()
    except: 
        statsd.increment('fetch_wind_error')
        logger.exception('fetch_wind()')
    try:
        with statsd.StatsdTimer('fetch_solar'): fetch_solar()
    except: 
        statsd.increment('fetch_solar_error')
        logger.exception('fetch_solar()')

schedule.every(INTERVAL_SECONDS).seconds.do(fetch_custom_countries)
schedule.every(INTERVAL_SECONDS).seconds.do(fetch_entsoe_countries)
schedule.every(15).minutes.do(fetch_weather)

fetch_custom_countries()
fetch_entsoe_countries()
fetch_weather()

while True:
    schedule.run_pending()
    time.sleep(10) # Only sleep for 10 seconds before checking again
