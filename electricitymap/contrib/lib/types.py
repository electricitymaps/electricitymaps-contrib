from typing import NewType

# ZoneKey is used throughout the code to identify zones.
# These are uppercase with 1-3 parts separated by dashes,
# where the first part is a two-letter country code,
# e.g. "AU", "AU-TAS", "AU-TAS-CBI".
ZoneKey = NewType("ZoneKey", str)
