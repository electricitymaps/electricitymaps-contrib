from json import loads
import pytest
from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
import requests_mock
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.JP_SK import get_nuclear_power_image_url, get_nuclear_power_value_and_timestamp_from_image_url


class TestWebaruba(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

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

    def test_find_nuclear_image_url(self):
        with requests_mock.Mocker() as mock:
            # Read the content of your saved HTML file
            saved_html_file = "./parsers/test/mocks/JP-SK/JP-SK_nuclear.html"
            with open(saved_html_file, "r") as file:
                html_content = file.read()

            # Set up the mock response using the HTML content
            mock.get("https://www.yonden.co.jp/energy/atom/ikata/ikt722.html", text=html_content)


            # Call the function that you want to test
            nuclear_url = get_nuclear_power_image_url("https://www.yonden.co.jp/energy/atom/ikata/ikt722.html", self.session)

            # Assert the result
            self.assertEqual(
                nuclear_url,
                "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221",
            )

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

# import os

# # Define a mock Session class for testing
# class MockSession:
#     def get(self, url):
#         class MockResponse:
#             def __init__(self, content):
#                 self.content = content

#         if url == "https://www.yonden.co.jp/energy/atom/ikata/ikt722.html":
#             return MockResponse("<html><body><img src='ikt721-1.gif'></body></html>")
#         elif url == "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221":
#             return MockResponse(b"Mocked image content")

# # Define the 'mock_session' fixture
# @pytest.fixture
# def mock_session():
#     return MockSession()


# def test_get_nuclear_power_image_url(mock_session):
#     # Read the saved HTML content from the file
#     with open(os.path.join("./parsers/test/mocks/JP-SK", "JP-SK_nuclear.html"), "r") as file:
#         html_content = file.read()

#     # Mock the response using the HTML content
#     img_url = get_nuclear_power_image_url("https://www.yonden.co.jp/energy/atom/ikata/ikt722.html", mock_session, html_content)
#     assert img_url == "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221"

# def test_get_nuclear_power_value_and_timestamp_from_image_url(mock_session):
#     # Read the saved image content from the file
#     with open(os.path.join("./parsers/test/mocks/JP-SK", "ikt721-1.gif"), "rb") as file:
#         image_content = file.read()

#     # Mock the response using the image content
#     nuclear_power, datetime_nuclear = get_nuclear_power_value_and_timestamp_from_image_url(
#         "https://www.yonden.co.jp/energy/atom/ikata/ikt721-1.gif?202309142221", mock_session, image_content
#     )
#     assert nuclear_power == 909.0  # Modify this value as needed
#     # assert datetime_nuclear.strftime("%Y-%m-%d %H:%M:%S%z") == "2023-09-14 22:21:00+0900"  # Modify as needed
