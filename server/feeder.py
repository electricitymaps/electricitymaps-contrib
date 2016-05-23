import pymongo
import schedule, time

from parsers.dk import fetch_dk

parsers = [fetch_dk]

client = pymongo.MongoClient('mongodb://localhost:27017')
db = client['electricity']
col = db['realtime']

def fetch_all():
    for parser in parsers: col.insert_one(parser())

schedule.every(1).minutes.do(fetch_all)

while True:
    schedule.run_pending()
    time.sleep(1)
