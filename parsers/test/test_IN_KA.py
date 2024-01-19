import unittest
from importlib import resources

from requests import Session
from requests_mock import GET, Adapter

from parsers import IN_KA


class Test_IN_KA(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("http://", self.adapter)

    def test_fetch_consumption(self):
        self.adapter.register_uri(
            GET,
            "http://kptclsldc.in/Default.aspx",
            text=resources.files("parsers.test.mocks")
            .joinpath("IN_KA_Default.html")
            .read_text(),
        )

        try:
            data = IN_KA.fetch_consumption("IN-KA", self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data["zoneKey"], "IN-KA")
            self.assertEqual(data["source"], "kptclsldc.in")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["consumption"])
            self.assertEqual(data["consumption"], 7430.0)
        except Exception as ex:
            self.fail(f"IN_KA.fetch_consumption() raised Exception: {ex.message}")

    def test_fetch_production(self):
        self.adapter.register_uri(
            GET,
            "http://kptclsldc.in/StateGen.aspx",
            text=resources.files("parsers.test.mocks")
            .joinpath("IN_KA_StateGen.html")
            .read_text(),
        )
        self.adapter.register_uri(
            GET,
            "http://kptclsldc.in/StateNCEP.aspx",
            text=resources.files("parsers.test.mocks")
            .joinpath("IN_KA_StateNCEP.html")
            .read_text(),
        )

        try:
            data = IN_KA.fetch_production("IN-KA", self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data["zoneKey"], "IN-KA")
            self.assertEqual(data["source"], "kptclsldc.in")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["production"])
            self.assertEqual(data["production"]["hydro"], 2434.0)
            self.assertIsNotNone(data["storage"])
        except Exception as ex:
            self.fail(f"IN_KA.fetch_production() raised Exception: {ex.message}")


if __name__ == "__main__":
    unittest.main()
