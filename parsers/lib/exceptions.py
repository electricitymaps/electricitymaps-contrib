class ParserException(Exception):
    """Parser Exception

    Args:
        parser (str): Parser name.
        message (str): String describing the exception.
        country_code (str): Country code or sortedCountryCodes.

    Attributes:
        parser (str): Parser name.
        message (str): String describing the exception.
        country_code (str): Country code or sortedCountryCodes."""

    def __init__(self, parser, message, country_code=None):
        super(ParserException, self).__init__(message)
        self.parser = parser
        self.country_code = country_code

    def __str__(self):
        if self.country_code:
            country_code_info = " ({0})".format(self.country_code)
        else:
            country_code_info = ""
        return "{0} Parser{1}: {2}".format(self.parser, country_code_info, self.message)
