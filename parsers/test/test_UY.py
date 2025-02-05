import re
from pathlib import Path

import pytest
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.UY import fetch_consumption, fetch_exchange, fetch_production


def test_fetch_production(adapter, session, snapshot):
    html = Path("parsers/test/mocks/UY/html.html")
    adapter.register_uri(
        GET,
        "https://pronos.adme.com.uy/gpf.php",
        text=html.read_text(),
    )
    data = Path("parsers/test/mocks/UY/data.ods")
    adapter.register_uri(
        GET,
        re.compile(r"https://pronos\.adme\.com\.uy.*cache.*"),
        content=data.read_bytes(),
    )
    assert snapshot == fetch_production(
        zone_key=ZoneKey("UY"),
        session=session,
    )


def test_fetch_consumption(adapter, session, snapshot):
    html = Path("parsers/test/mocks/UY/html.html")
    adapter.register_uri(
        GET,
        "https://pronos.adme.com.uy/gpf.php",
        text=html.read_text(),
    )
    data = Path("parsers/test/mocks/UY/data.ods")
    adapter.register_uri(
        GET,
        re.compile(r"https://pronos\.adme\.com\.uy.*cache.*"),
        content=data.read_bytes(),
    )
    assert snapshot == fetch_consumption(
        zone_key=ZoneKey("UY"),
        session=session,
    )


@pytest.mark.parametrize("zone_key", [ZoneKey("AR"), ZoneKey("BR-S")])
def test_fetch_exchange(adapter, session, snapshot, zone_key):
    html = Path("parsers/test/mocks/UY/html.html")
    adapter.register_uri(
        GET,
        "https://pronos.adme.com.uy/gpf.php",
        text=html.read_text(),
    )
    data = Path("parsers/test/mocks/UY/data.ods")
    adapter.register_uri(
        GET,
        re.compile(r"https://pronos\.adme\.com\.uy.*cache.*"),
        content=data.read_bytes(),
    )
    assert snapshot == fetch_exchange(
        zone_key1=ZoneKey("UY"),
        zone_key2=zone_key,
        session=session,
    )
