import datetime
import warnings

import arrow


class ValidationError(ValueError):
    pass


def validate_reasonable_time(item, k):
    data_time = arrow.get(item['datetime'])
    if data_time.year < 2000:
        raise ValidationError("Data from %s can't be before year 2000, it was "
                              "%s" % (k, data_time))

    arrow_now = arrow.utcnow()
    if data_time > arrow_now:
        raise ValidationError(
            "Data from %s can't be in the future, data was %s, now is "
            "%s" % (k, data_time, arrow_now))


def validate_consumption(obj, zone_key):
    # Data quality check
    if obj['consumption'] is not None and obj['consumption'] < 0:
        raise ValidationError('%s: consumption has negative value '
                              '%s' % (zone_key, obj['consumption']))
    validate_reasonable_time(obj, zone_key)


def validate_exchange(item, k):
    if item.get('sortedZoneKeys', None) != k:
        raise ValidationError("Sorted country codes %s and %s don't "
                              "match" % (item.get('sortedZoneKeys', None), k))
    if 'datetime' not in item:
        raise ValidationError('datetime was not returned for %s' % k)
    if type(item['datetime']) != datetime.datetime:
        raise ValidationError('datetime %s is not valid for %s' %
                              (item['datetime'], k))
    validate_reasonable_time(item, k)


def validate_production(obj, zone_key):
    if 'datetime' not in obj:
        raise ValidationError(
            'datetime was not returned for %s' % zone_key)
    if 'countryCode' in obj:
        warnings.warn('object has field `countryCode`. It should have '
                      '`zoneKey` instead. In {}'.format(obj))
    if 'zoneKey' not in obj and 'countryCode' not in obj:
        raise ValidationError('zoneKey was not returned for %s' % zone_key)
    if not isinstance(obj['datetime'], datetime.datetime):
        raise ValidationError('datetime %s is not valid for %s' %
                              (obj['datetime'], zone_key))
    if (obj.get('zoneKey', None) or obj.get('countryCode', None)) != zone_key:
        raise ValidationError("Zone keys %s and %s don't match in %s" %
                              (obj.get('zoneKey', None), zone_key, obj))

    if ((obj.get('production', {}).get('unknown', None) is None and
         obj.get('production', {}).get('coal', None) is None and
         obj.get('production', {}).get('oil', None) is None and
         obj.get('production', {}).get('gas', None) is None and zone_key
         not in ['CH', 'NO', 'AUS-TAS', 'DK-BHM', 'US-NEISO'])):
        raise ValidationError(
            "Coal, gas or oil or unknown production value is required for"
            " %s" % zone_key)
    if 'storage' in obj:
        if not isinstance(obj['storage'], dict):
            raise ValidationError('storage value must be a dict, was '
                                  '{}'.format(obj['storage']))
        not_allowed_keys = set(obj['storage']) - {'battery', 'hydro'}
        if not_allowed_keys:
            raise ValidationError('unexpected keys in storage: {}'.format(
                not_allowed_keys))
    for k, v in obj['production'].items():
        if v is None:
            continue
        if v < 0:
            raise ValidationError('%s: key %s has negative value %s' %
                                  (zone_key, k, v))
    validate_reasonable_time(obj, zone_key)
