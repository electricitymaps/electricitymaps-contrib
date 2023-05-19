import json
import unittest

import pandas as pd
from pkg_resources import resource_filename, resource_string
from requests import Session
from requests_mock import Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers import IN_WE


class Test_IN_WE(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.test_package = "parsers.test.mocks"
        self.session.mount("https://", self.adapter)

        response_consumption_json = json.loads(
            resource_string(self.test_package, "IN_WE_consumption_data.json")
        )
        self.adapter.register_uri(
            "POST", IN_WE.CONSUMPTION_URL, json=response_consumption_json
        )
        self.consumption_result_file_path = resource_filename(
            self.test_package, "IN_WE_fetch_consumption_result.txt"
        )

        response_exchange_json = json.loads(
            resource_string(self.test_package, "IN_SO->IN_WE_exchange_data.json")
        )
        self.adapter.register_uri(
            "POST", IN_WE.EXCHANGE_URL, json=response_exchange_json
        )
        self.exchange_result_file_path = resource_filename(
            self.test_package, "IN_SO->IN_WE_fetch_exchange_result.txt"
        )

    def test_fetch_consumption(self):
        try:
            result = IN_WE.fetch_consumption(
                zone_key=ZoneKey("IN-WE"), session=self.session
            )
            expected_result = pd.read_pickle(self.consumption_result_file_path)
            self.assertEqual(expected_result, result)
        except Exception as ex:
            self.fail("IN_WE.fetch_consumption() raised Exception: {0}".format(ex))

    def test_fetch_exchange(self):
        try:
            result = IN_WE.fetch_exchange(
                zone_key1=ZoneKey("IN-SO"),
                zone_key2=ZoneKey("IN-WE"),
                session=self.session,
            )
            expected_result = pd.read_pickle(self.exchange_result_file_path)
            self.assertEqual(expected_result, result)
        except Exception as ex:
            self.fail("IN_WE.fetch_exchange() raised Exception: {0}".format(ex))


if __name__ == "__main__":
    unittest.main()
