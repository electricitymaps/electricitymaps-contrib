import unittest

from mock import patch
from ree import BalearicIslands, Formentera, Response
from requests import Session

from parsers import ES_IB


class TestESIB(unittest.TestCase):
    def setUp(self):
        self.session = Session()

        first_request = Response(1504603773)
        first_request.link["pe_ma"] = 50
        first_request.link["ib_fo"] = 10

        second_request = Response(1504603842)
        second_request.link["pe_ma"] = 50
        second_request.link["ib_fo"] = 10

        self.mocked_responses = [first_request, second_request]

    @patch.object(BalearicIslands, "get_all")
    def test_fetch_consumption(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES_IB.fetch_consumption("ES-IB", self.session)
        self.assertIsNotNone(data_list)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-IB")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["consumption"])

    @patch.object(Formentera, "get_all")
    def test_fetch_consumption_ES_IB_FO(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES_IB.fetch_consumption("ES-IB-FO", self.session)
        self.assertIsNotNone(data_list)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-IB-FO")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["consumption"])

    @patch.object(BalearicIslands, "get_all")
    def test_fetch_production(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES_IB.fetch_production("ES-IB", self.session)
        self.assertIsNotNone(data_list)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-IB")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["production"])
            self.assertIsNotNone(data["storage"])

    @patch.object(Formentera, "get_all")
    def test_fetch_production_ES_IB_FO(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES_IB.fetch_production("ES-IB-FO", self.session)
        self.assertIsNotNone(data_list)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-IB-FO")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["datetime"])
            self.assertIsNotNone(data["production"])
            self.assertIsNotNone(data["storage"])

    @patch.object(BalearicIslands, "get_all")
    def test_fetch_exchange(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES_IB.fetch_exchange("ES", "ES-IB", self.session)
        self.assertIsNotNone(data_list)
        for data in data_list:
            self.assertEqual(data["sortedZoneKeys"], "ES->ES-IB")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["netFlow"])
            self.assertEqual(data["netFlow"], 50.0)
            self.assertIsNotNone(data["datetime"])

    @patch.object(Formentera, "get_all")
    def test_fetch_exchange_ES_IB_FO(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES_IB.fetch_exchange("ES-IB-FO", "ES-IB-IZ", self.session)
        self.assertIsNotNone(data_list)
        for data in data_list:
            self.assertEqual(data["sortedZoneKeys"], "ES-IB-FO->ES-IB-IZ")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["netFlow"])
            self.assertEqual(data["netFlow"], -10.0)
            self.assertIsNotNone(data["datetime"])


if __name__ == "__main__":
    unittest.main()
