from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.JP_SK import get_nuclear_power_image_url, get_nuclear_power_from_image_url


class TestWebaruba(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_find_nuclear_image_url(self):
        """we want to assert that the image url is the correct one"""
        nuclear_production_html = resource_string("parsers.test.mocks.JP-SK", "JP-SK_nuclear.html")
        self.adapter.register_uri(
            GET,
            ANY,
            content=nuclear_production_html,
        )
        nuclear_url = get_nuclear_power_image_url(
            "https://test", self.session
        )
        self.assertEqual(nuclear_url, "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221")

    def test_fetch_nuclear_image(self):
        nuclear_prod_image = resource_string("parsers.test.mocks.JP-SK", "ikt721-1.gif")
        self.adapter.register_uri(
            GET,
            ANY,
            content=nuclear_prod_image,
        )
        nuclear_production = get_nuclear_power_from_image_url(
            "https://test", self.session
        )
        self.assertEqual(nuclear_production, 909.0)

