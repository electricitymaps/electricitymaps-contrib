import pymongo
import logging, os, schedule, time

from parsers.DE import fetch_DE
from parsers.DK import fetch_DK
from parsers.ES import fetch_ES
from parsers.FI import fetch_FI
from parsers.FR import fetch_FR
from parsers.GB import fetch_GB
from parsers.NO import fetch_NO
from parsers.SE import fetch_SE

from parsers.solar import fetch_solar
from parsers.wind import fetch_wind

INTERVAL_SECONDS = 60 * 5

parsers = [
    fetch_DE,
    fetch_DK,
    fetch_ES,
    fetch_FI,
    fetch_FR,
    fetch_GB,
    fetch_NO,
    fetch_SE
]

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

client = pymongo.MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
db = client['electricity']
col = db['realtime']

def fetch_countries():
    for parser in parsers: 
        try:
            obj = parser()
            logging.info('INSERT %s' % obj)
            col.insert_one(obj)
        except: logger.exception('fetch_one_country')

def fetch_weather():
    try:
        fetch_wind()
    except: logger.exception('fetch_wind()')
    try:
        fetch_solar()
    except: logger.exception('fetch_solar()')

schedule.every(INTERVAL_SECONDS).seconds.do(fetch_countries)
schedule.every(6).hours.do(fetch_weather)

fetch_countries()
fetch_weather()

while True:
    schedule.run_pending()
    time.sleep(INTERVAL_SECONDS)
