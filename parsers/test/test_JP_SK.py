import datetime
import re

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from parsers.JP_SK import (
    NUCLEAR_REPORT_URL,
    get_nuclear_power_image_url,
    get_nuclear_power_value_and_timestamp_from_image_url,
)


class TestJapanShikokuNuclear(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_find_nuclear_image_url(self):
        with open(
            "./parsers/test/mocks/JP-SK/jp-sk-nuclear-html-page.html", "rb"
        ) as report_byte_content:
            self.adapter.register_uri(
                GET, NUCLEAR_REPORT_URL, content=report_byte_content.read()
            )
        image_url = get_nuclear_power_image_url(self.session)
        pattern = r"(?P<filename>ikt721-1\.gif\?[0-9]{12})"
        pattern_matches = re.findall(pattern, image_url)

        assert len(pattern_matches) == 1
        assert pattern_matches[0] == "ikt721-1.gif?202402060021"

    def test_fetch_nuclear_image(self):
        nuclear_prod_image = resource_string("parsers.test.mocks.JP-SK", "image3.gif")
        self.adapter.register_uri(
            GET,
            ANY,
            content=nuclear_prod_image,
        )
        (
            nuclear_production,
            nuclear_timestamp,
        ) = get_nuclear_power_value_and_timestamp_from_image_url(
            "https://test-url/ikt721-1.gif?202402062021", self.session
        )

        self.assertIsInstance(nuclear_production, float)
        self.assertIsInstance(nuclear_timestamp, datetime.datetime)
        self.assertEqual(nuclear_production, 918.0)
