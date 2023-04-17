import logging


class ParserLoggerAdapter(logging.LoggerAdapter):
    """
    Converts log usage from string to dict and adds zone key, parser to the dict.
    """

    def process(self, msg, kwargs):
        # handle if msg is already a dict
        if isinstance(msg, dict) and "message" in msg:
            message = msg["message"]
        else:
            message = msg

        # Supports extra dict when logging
        extra = kwargs.get("extra", {})
        new_dict = {"message": message, "zone_key": self.extra["zone_key"], "parser": self.extra["parser"], **extra}

        return new_dict, kwargs