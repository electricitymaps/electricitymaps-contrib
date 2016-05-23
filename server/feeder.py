import pymongo
import schedule, time

from parsers.DK import fetch_DK

INTERVAL_SECONDS = 60

parsers = [fetch_DK]

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['electricity']
col = db['realtime']

def fetch_all():
    for parser in parsers: 
        obj = parser()
        print 'INSERT %s' % obj
        col.insert_one(obj)

schedule.every(INTERVAL_SECONDS).seconds.do(fetch_all)

while True:
    schedule.run_pending()
    time.sleep(INTERVAL_SECONDS)
