class ParserException(Exception):
    """Parser Exception

    Args:
        parser (str): Parser name.
        message (str): String describing the exception.
        zone_key (str | None): Country code or sortedZoneKeys.

    Attributes:
        parser (str): Parser name.
        message (str): String describing the exception.
        zone_key (str | None): Country code or sortedZoneKeys."""

    def __init__(self, parser: str, message: str, zone_key: str | None = None):
        super().__init__(message)
        self.parser = parser
        self.zone_key = zone_key

    def __str__(self):
        zone_key_info = f" ({self.zone_key})" if self.zone_key else ""
        return f"{self.parser} Parser{zone_key_info}: {self.args[0]}"
