import arrow, datetime

def validate_consumption(obj, country_code):
    # Data quality check
    if obj['consumption'] is not None and obj['consumption'] < 0:
        raise ValueError('%s: consumption has negative value %s' % (country_code, obj['consumption']))

def validate_exchange(item, k):
    if item.get('sortedCountryCodes', None) != k:
        raise Exception("Sorted country codes %s and %s don't match" % (item.get('sortedCountryCodes', None), k))
    if not 'datetime' in item:
        raise Exception('datetime was not returned for %s' % k)
    if not type(item['datetime']) == datetime.datetime:
        raise Exception('datetime %s is not valid for %s' % (item['datetime'], k))
    if arrow.get(item['datetime']) > arrow.now():
        raise Exception("Data from %s can't be in the future" % k)

def validate_production(obj, country_code):
    if not 'datetime' in obj:
        raise Exception('datetime was not returned for %s' % country_code)
    if not 'countryCode' in obj:
        raise Exception('countryCode was not returned for %s' % country_code)
    if not type(obj['datetime']) == datetime.datetime:
        raise Exception('datetime %s is not valid for %s' % (obj['datetime'], country_code))
    if obj.get('countryCode', None) != country_code:
        raise Exception("Country codes %s and %s don't match" % (obj.get('countryCode', None), country_code))
    if arrow.get(obj['datetime']) > arrow.now():
        raise Exception("Data from %s can't be in the future" % country_code)
    if obj.get('production', {}).get('unknown', None) is None and \
        obj.get('production', {}).get('coal', None) is None and \
        obj.get('production', {}).get('oil', None) is None and \
        country_code not in ['CH', 'NO', 'AUS-TAS']:
        raise Exception("Coal or oil or unknown production value is required for %s" % (country_code))
    for k, v in obj['production'].iteritems():
        if v is None: continue
        if v < 0: raise ValueError('%s: key %s has negative value %s' % (country_code, k, v))
