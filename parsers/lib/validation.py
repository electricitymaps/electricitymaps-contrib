#!/usr/bin/env python3

"""Centralised validation function for all parsers."""


def validate(datapoint, **kwargs):
    """
    Validates a production datapoint based on given constraints.
    If the datapoint is found to be invalid then None is returned.

    Arguments
    ---------
    datapoint: a production datapoint. See examples
    optional keyword arguments
      required: list
        Generation types that must be present.
        For example ['gas', 'hydro']
        If any of these types are None the datapoint will be invalidated.
        Defaults to an empty list.
      floor: float
        Checks production sum is above floor value.
        If this is not the case the datapoint is invalidated.
        Defaults to None
      expected_range: tuple
        Checks production total against expected range.
        Tuple is in form (low threshold, high threshold).
        For example (1800, 12000)
        If the total is outside this range the datapoint will be invalidated.
        Defaults to None.

    Examples
    --------
    >>> test_datapoint = {
    >>>   'countryCode': 'FR',
    >>>   'datetime': '2017-01-01T00:00:00Z',
    >>>       'production': {
    >>>           'biomass': 50.0,
    >>>           'coal': 478.0,
    >>>           'gas': 902.7,
    >>>           'hydro': 190.1,
    >>>           'nuclear': None,
    >>>           'oil': 0.0,
    >>>           'solar': 20.0,
    >>>           'wind': 40.0,
    >>>           'geothermal': 0.0,
    >>>           'unknown': 6.0
    >>>       },
    >>>       'storage': {
    >>>           'hydro': -10.0,
    >>>       },
    >>>       'source': 'mysource.com'
    >>> }

    >>> validate(datapoint, required=['gas'], expected_range=(100, 2000))
    datapoint
    >>> validate(datapoint, required=['not_a_production_type'])
    None
    """

    required = kwargs.pop('required', [])
    floor = kwargs.pop('floor', False)
    expected_range = kwargs.pop('expected_range', None)
    if kwargs:
        raise TypeError('Unexpected **kwargs: %r' % kwargs)

    generation = datapoint['production']

    if required:
        for item in required:
            if generation.get(item, None) is None:
                print("Required generation type {} is missing from {}".format(
                    item, datapoint['countryCode']))
                return None

    if floor:
        total = sum(v for k, v in generation.items() if v is not None)
        if total < floor:
            print("{} reported total of {}MW does not meet {}MW floor value".format(
                datapoint['countryCode'], total, floor))
            return None

    if expected_range:
        low = min(expected_range)
        high = max(expected_range)
        total = sum(v for k, v in generation.items() if v is not None)
        if low <= total <= high:
            pass
        else:
            print("{} reported total of {}MW falls outside range of {}".format(
                datapoint['countryCode'], total, expected_range))
            return None

    return datapoint


test_datapoint = {
    'countryCode': 'FR',
    'datetime': '2017-01-01T00:00:00Z',
    'production': {
        'biomass': 50.0,
        'coal': 478.0,
        'gas': 902.7,
        'hydro': 190.1,
        'nuclear': None,
        'oil': 0.0,
        'solar': 20.0,
        'wind': 40.0,
        'geothermal': 0.0,
        'unknown': 6.0
    },
    'storage': {
        'hydro': -10.0,
    },
    'source': 'mysource.com'
}

if __name__ == '__main__':
    print(validate(test_datapoint, required=['gas'], expected_range=(100, 2000)))
