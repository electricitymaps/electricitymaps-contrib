import pymongo
import schedule, time

from parsers.DE import fetch_DE
from parsers.DK import fetch_DK
from parsers.ES import fetch_ES
from parsers.FI import fetch_FI
from parsers.FR import fetch_FR
from parsers.GB import fetch_GB
from parsers.NO import fetch_NO
from parsers.SE import fetch_SE

from parsers.solar import fetch_solar

INTERVAL_SECONDS = 60

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

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['electricity']
col = db['realtime']

def fetch_all():
    for parser in parsers: 
        obj = parser()
        print 'INSERT %s' % obj
        col.insert_one(obj)

schedule.every(INTERVAL_SECONDS).seconds.do(fetch_all)
schedule.every(6).hours.do(fetch_solar)
fetch_all()

while True:
    schedule.run_pending()
    time.sleep(INTERVAL_SECONDS)
