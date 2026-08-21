import pytest

from electricitymap.contrib.parsers.lib import zonekey
from electricitymap.contrib.parsers.lib.exceptions import ParserException


def test_assert_zone_key():
    zonekey.assert_zone_key("ES", "ES", "ESIOS")

    with pytest.raises(ParserException) as exc_info:
        zonekey.assert_zone_key("ES", "ES-IB")
    assert str(exc_info.value) == "ES Parser (ES): zone_key expected ES-IB, is ES"

    with pytest.raises(ParserException) as exc_info:
        zonekey.assert_zone_key("ES", "ES-IB", "ESIOS")
    assert str(exc_info.value) == "ESIOS Parser (ES): zone_key expected ES-IB, is ES"
