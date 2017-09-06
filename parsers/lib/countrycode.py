from parsers.lib.exceptions import ParserException


def assert_country_code(country_code, expected, parser_name=None):
    """Assert country code"""
    if not country_code or country_code != expected:
        if not parser_name:
            parser_name = country_code
        raise ParserException(parser_name, 'Country_code expected {0}, is {1}'.format(expected, country_code), country_code)
