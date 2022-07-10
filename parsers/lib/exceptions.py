from typing import Union

from electricitymap.contrib.config import ZoneKey


class ParserException(Exception):
    """Parser Exception

    Args:
        parser (str): Parser name.
        message (str): String describing the exception.
        zone_key (str): Country code or sortedZoneKeys.

    Attributes:
        parser (str): Parser name.
        message (str): String describing the exception.
        zone_key (str): Country code or sortedZoneKeys."""

    def __init__(self, parser: str, message: str, zone_key: Union[ZoneKey, None]=None):
        super(ParserException, self).__init__(message)
        self.parser = parser
        self.zone_key = zone_key

    def __str__(self):
        if self.zone_key:
            zone_key_info = " ({0})".format(self.zone_key)
        else:
            zone_key_info = ""
        return "{0} Parser{1}: {2}".format(self.parser, zone_key_info, self.args[0])
