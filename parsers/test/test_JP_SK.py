from json import loads

import pytest
import requests_mock
from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase
from requests import Session
from requests_mock import GET, POST, Adapter
import re
from PIL import Image
from io import BytesIO
from electricitymap.contrib.lib.types import ZoneKey
from parsers.JP_SK import (
    NUCLEAR_REPORT_URL,
    get_nuclear_power_image_url,
    get_nuclear_power_value_and_timestamp_from_image_url,
)


def test_find_nuclear_image_url():
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)

    report_byte_content = open("./parsers/test/mocks/JP-SK/JP-SK_nuclear.html", "rb")
    adapter.register_uri(GET, NUCLEAR_REPORT_URL, content=report_byte_content.read())

    image_url = get_nuclear_power_image_url(session)

    pattern=r"(?P<filename>ikt721-1\.gif\?[0-9]{12})"
    pattern_matches = re.findall(pattern, image_url)
    assert len(pattern_matches) == 1
    assert pattern_matches[0] == "ikt721-1.gif?202310132235"

def test_get_nuclear_power_value_and_timestamp_from_image_url():
    session = Session()
    adapter = Adapter()
    session.mount("https://", adapter)

    LINK = "https://www.toto.tata"

    image = Image.open("./parsers/test/mocks/JP-SK/ikt721-1.gif")
    width, height = image.size
    image = image.crop((0, 0, width, height))
    adapter.register_uri(GET, LINK, content=image.tobytes())

    production_nuclear, ts = get_nuclear_power_value_and_timestamp_from_image_url(LINK, session)



###### old version using unittest - to be removed
# class TestWebaruba(TestCase):
#     def setUp(self) -> None:
#         self.session = Session()
#         self.adapter = Adapter()
#         self.session.mount("https://", self.adapter)

    # def test_find_nuclear_image_url(self):
    #     """we want to assert that the image url is the correct one"""
    #     nuclear_production_html = resource_string(
    #         "parsers.test.mocks.JP-SK", "JP-SK_nuclear.html"
    #     )
    #     self.adapter.register_uri(
    #         GET,
    #         ANY,
    #         content=nuclear_production_html,
    #     )
    #     nuclear_url = get_nuclear_power_image_url("https://test", self.session)
    #     breakpoint()
    #     self.assertEqual(
    #         nuclear_url,
    #         "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221",
    #     )

    # def test_find_nuclear_image_url(self):
    #     with requests_mock.Mocker() as mock:
    #         # Read the content of your saved HTML file
    #         saved_html_file = "./parsers/test/mocks/JP-SK/JP-SK_nuclear.html"
    #         with open(saved_html_file, "r") as file:
    #             html_content = file.read()

    #         # Set up the mock response using the HTML content
    #         mock.get(
    #             "https://www.yonden.co.jp/energy/atom/ikata/ikt722.html",
    #             text=html_content,
    #         )

    #         # Call the function that you want to test
    #         nuclear_url = get_nuclear_power_image_url(
    #             "https://www.yonden.co.jp/energy/atom/ikata/ikt722.html", self.session
    #         )

    #         # Assert the result
    #         self.assertEqual(
    #             nuclear_url,
    #             "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221",
    #         )

    # def test_fetch_nuclear_image(self):
    #     nuclear_prod_image = resource_string("parsers.test.mocks.JP-SK", "ikt721-1.gif")
    #     self.adapter.register_uri(
    #         GET,
    #         ANY,
    #         content=nuclear_prod_image,
    #     )
    #     nuclear_production, nuclear_timestamp = get_nuclear_power_value_and_timestamp_from_image_url(
    #         "https://test", self.session
    #     )
    #     self.assertEqual(nuclear_production, 909.0)
