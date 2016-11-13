import pymongo

def migrate(db):
    print 'Starting data migration..'
    # ** Migrate one collection (production) to two (production & exchanges)
    col_production = db['production']
    col_exchange = db['exchange']
    col_old = db['realtime']
    for row in col_old.find():
        # Extract exchange
        if 'exchange' in row:
            exchange = row['exchange']
            # Insert into exchange db
            for k, v in exchange.iteritems():
                sortedCountryCodes = '->'.join(sorted([k, row['countryCode']]))
                col_exchange.insert({
                    'datetime': row.get('datetimeExchange', row['datetime']),
                    'sortedCountryCodes': sortedCountryCodes,
                    'netFlow': v if sortedCountryCodes[1] == k else v * -1
                })
            # Delete exchange
            del row['exchange']
            if 'datetimeExchange' in row: del row['datetimeExchange']
            if 'datetimeProduction' in row: del row['datetimeProduction']
        # Copy in other collection
        try: col_production.insert(row)
        except pymongo.errors.DuplicateKeyError: pass
        # Delete in old collection
        col_old.remove({'_id': row['_id']})
    print 'Migration done.'
