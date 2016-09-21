import glob
import pymongo
import logging, os, schedule, time

from parsers.solar import fetch_solar
from parsers.wind import fetch_wind

INTERVAL_SECONDS = 60 * 5

# Import all country parsers
def import_country(country_code):
    return getattr(
        __import__('parsers.%s' % country_code, globals(), locals(), ['fetch_%s' % country_code]),
        'fetch_%s' % country_code)
country_codes = map(lambda s: s[len('parsers/'):len('parsers/')+2], glob.glob('parsers/??.py'))
parsers = map(import_country, country_codes)

# Set up stats
import statsd
statsd.init_statsd({
    'STATSD_HOST': os.environ.get('STATSD_HOST', 'localhost'),
    'STATSD_BUCKET_PREFIX': 'electricymap_feeder'
})

# Set up logging
ENV = os.environ.get('ENV', 'development').lower()
logger = logging.getLogger(__name__)
if not ENV == 'development':
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(
        mailhost=('smtp.mailgun.org', 587),
        fromaddr='Application Bug Reporter <noreply@mailgun.com>',
        toaddrs=['olivier.corradi@gmail.com'],
        subject='Electricity Map Feeder Error',
        credentials=(os.environ.get('MAILGUN_USER'), os.environ.get('MAILGUN_PASSWORD'))
    )
    mail_handler.setLevel(logging.ERROR)
    logger.addHandler(mail_handler)
    logging.getLogger('statsd').addHandler(logging.StreamHandler())
else: logger.addHandler(logging.StreamHandler())


client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client['electricity']
col = db['realtime']

def fetch_countries():
    for parser in parsers: 
        try:
            with statsd.StatsdTimer('fetch_one_country'):
                obj = parser()
                logging.info('INSERT %s' % obj)
                col.insert_one(obj)
        except: 
            statsd.increment('fetch_one_country_error')
            logger.exception('fetch_one_country()')

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

schedule.every(INTERVAL_SECONDS).seconds.do(fetch_countries)
schedule.every(15).minutes.do(fetch_weather)

fetch_countries()
fetch_weather()

while True:
    schedule.run_pending()
    time.sleep(INTERVAL_SECONDS)
