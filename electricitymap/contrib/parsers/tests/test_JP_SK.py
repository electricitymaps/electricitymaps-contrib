import datetime
import re
from importlib import resources

from requests_mock import ANY, GET

from electricitymap.contrib.parsers.JP_SK import (
    NUCLEAR_REPORT_URL,
    get_nuclear_power_image_url,
    get_nuclear_power_value_and_timestamp_from_image_url,
)


def test_find_nuclear_image_url(adapter, session):
    report_content = (
        resources.files("electricitymap.contrib.parsers.tests.mocks.JP-SK")
        .joinpath("jp-sk-nuclear-html-page.html")
        .read_bytes()
    )
    adapter.register_uri(GET, NUCLEAR_REPORT_URL, content=report_content)
    image_url = get_nuclear_power_image_url(session)
    pattern = r"(?P<filename>ikt721-1\.gif\?[0-9]{12})"
    pattern_matches = re.findall(pattern, image_url)

    assert len(pattern_matches) == 1
    assert pattern_matches[0] == "ikt721-1.gif?202402060021"


def test_fetch_nuclear_image(adapter, session):
    nuclear_prod_image = (
        resources.files("electricitymap.contrib.parsers.tests.mocks.JP-SK")
        .joinpath("image3.gif")
        .read_bytes()
    )
    adapter.register_uri(
        GET,
        ANY,
        content=nuclear_prod_image,
    )
    (
        nuclear_production,
        nuclear_timestamp,
    ) = get_nuclear_power_value_and_timestamp_from_image_url(
        "https://test-url/ikt721-1.gif?202402062021", session
    )

    assert isinstance(nuclear_production, float)
    assert isinstance(nuclear_timestamp, datetime.datetime)
    assert nuclear_production == 918.0
