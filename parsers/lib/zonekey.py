from .exceptions import ParserException

def assert_zone_key(zone_key, expected, parser_name=None):
    """Assert country code"""
    if not zone_key or zone_key != expected:
        if not parser_name:
            parser_name = zone_key
        raise ParserException(parser_name, 'zone_key expected {0}, is {1}'.format(expected, zone_key), zone_key)
