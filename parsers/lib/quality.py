import datetime

import arrow


class ValidationError(ValueError):
    pass


def validate_consumption(obj, zone_key):
    # Data quality check
    if obj['consumption'] is not None and obj['consumption'] < 0:
        raise ValidationError('%s: consumption has negative value '
                                  '%s' % (zone_key, obj['consumption']))


def validate_exchange(item, k):
    if item.get('sortedZoneKeys', None) != k:
        raise ValidationError("Sorted country codes %s and %s don't "
                                  "match" % (item.get('sortedZoneKeys', None),
                                             k))
    if 'datetime' not in item:
        raise ValidationError('datetime was not returned for %s' % k)
    if type(item['datetime']) != datetime.datetime:
        raise ValidationError('datetime %s is not valid for %s' %
                              (item['datetime'], k))
    data_time = arrow.get(item['datetime'])
    if data_time > arrow.now():
        raise ValidationError("Data from %s can't be in the future, data was "
                              "%s, now is %s" % (k, data_time, arrow.now()))
    if data_time.year < 2000:
        raise ValidationError("Data from %s can't be before year 2000, it was "
                              "%s" % (k, data_time))


def validate_production(obj, zone_key):
    if 'datetime' not in obj:
        raise ValidationError(
            'datetime was not returned for %s' % zone_key)
    if 'zoneKey' not in obj:
        raise ValidationError('zoneKey was not returned for %s' % zone_key)
    if type(obj['datetime']) != datetime.datetime:
        raise ValidationError('datetime %s is not valid for %s' %
                              (obj['datetime'], zone_key))
    if obj.get('zoneKey', None) != zone_key:
        raise ValidationError("Country codes %s and %s don't match" %
                              (obj.get('zoneKey', None), zone_key))
    data_time = arrow.get(obj['datetime'])
    if data_time > arrow.now():
        raise ValidationError(
            "Data from %s can't be in the future, data was %s, now is "
            "%s" % (zone_key, data_time, arrow.now()))

    if (obj.get('production', {}).get('unknown', None) is None and
        obj.get('production', {}).get('coal', None) is None and
        obj.get('production', {}).get('oil', None) is None and
        obj.get('production', {}).get('gas', None) is None and
        zone_key not in ['CH', 'NO', 'AUS-TAS', 'DK-BHM', 'US-NEISO']):
            raise ValidationError(
                "Coal or oil or unknown production value is required for"
                " %s" % (zone_key))
    for k, v in obj['production'].items():
        if v is None:
            continue
        if v < 0:
            raise ValidationError('%s: key %s has negative value %s' %
                                  (zone_key, k, v))
