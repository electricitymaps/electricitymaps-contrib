import unittest
from importlib import resources

from requests import Session
from requests_mock import ANY, Adapter

from parsers.archived import IN_AP


class Test_IN_AP(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        self.adapter.register_uri(
            ANY,
            ANY,
            text=resources.files("parsers.test.mocks")
            .joinpath("IN_AP.html")
            .read_text(),
        )

    def test_fetch_production(self):
        try:
            data = IN_AP.fetch_production("IN-AP", self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data["zoneKey"], "IN-AP")
            self.assertEqual(data["source"], "core.ap.gov.in")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["production"])
            self.assertIsNotNone(data["storage"])
        except Exception as ex:
            self.fail(f"IN_AP.fetch_production() raised Exception: {ex}")

    def test_fetch_consumption(self):
        try:
            data = IN_AP.fetch_consumption("IN-AP", self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data["zoneKey"], "IN-AP")
            self.assertEqual(data["source"], "core.ap.gov.in")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["consumption"])
        except Exception as ex:
            self.fail(f"IN_AP.fetch_consumption() raised Exception: {ex}")


if __name__ == "__main__":
    unittest.main()
