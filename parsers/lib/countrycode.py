def assert_country_code(country_code, expected):
    """Assert country code"""
    if not country_code or country_code != expected:
        raise Exception('{0} Parser country_code isn\'t {0}, is {1}'.format(expected, country_code))
