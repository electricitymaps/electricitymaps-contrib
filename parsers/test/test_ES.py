from datetime import datetime, timezone
from unittest import TestCase, main

from mock import patch
from ree import ElHierro, Formentera, Mallorca, Response
from requests import Session

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ES


class TestES(TestCase):
    def setUp(self):
        self.session = Session()

        first_request = Response(15046037)
        first_request.link["pe_ma"] = 50
        first_request.link["ib_fo"] = 10

        second_request = Response(15046038)
        second_request.link["pe_ma"] = 50
        second_request.link["ib_fo"] = 10

        self.mocked_responses = [first_request, second_request]

    ### El Hierro
    # Consumption
    @patch.object(ElHierro, "get_all")
    def test_fetch_consumption(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES.fetch_consumption(ZoneKey("ES-CN-HI"), self.session)
        self.assertIsNot(data_list, [])
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-CN-HI")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(15046037).astimezone(timezone.utc),
            )
            self.assertIsNotNone(data["consumption"])

    # Production
    @patch.object(ElHierro, "get_all")
    def test_fetch_production_el_hierro(self, mocked_get_all):
        mocked_get_all.return_value = (
            Response(15146298, 10.0, 10, 5, 13, 3, 4, 3.5, 10, 5, 0, 3),
        )
        data_list = ES.fetch_production("ES-CN-HI", self.session)
        self.assertIsNot(data_list, [])
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-CN-HI")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertIsNotNone(data["production"])
            self.assertIsNotNone(data["storage"])
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(15146298).astimezone(timezone.utc),
            )
            self.assertEqual(data["production"]["gas"], 0)
            self.assertEqual(data["production"]["oil"], 22)
            self.assertEqual(data["production"]["hydro"], 0)
            self.assertEqual(data["production"]["solar"], 3.5)
            self.assertEqual(data["production"]["wind"], 13)
            self.assertEqual(data["production"]["coal"], 5)
            self.assertEqual(data["production"]["unknown"], 3)
            self.assertEqual(data["storage"]["hydro"], -10)

    ### Formentera
    # Production
    @patch.object(Formentera, "get_all")
    def test_fetch_production_ES_IB_FO(self, mocked_get_all):
        mocked_get_all.return_value = (
            Response(15146298, 10.0, 10, 5, 13, 3, 4, 3.5, 10, 5, 0, 3),
        )
        data_list = ES.fetch_production("ES-IB-FO", self.session)
        self.assertIsNot(data_list, [])
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-IB-FO")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertIsNot(data["production"], {})
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(15146298).astimezone(timezone.utc),
            )
            self.assertEqual(data["production"]["gas"], 8)
            self.assertEqual(data["production"]["oil"], 14)
            self.assertEqual(data["production"]["hydro"], 10)
            self.assertEqual(data["production"]["solar"], 3.5)
            self.assertEqual(data["production"]["wind"], 13)
            self.assertEqual(data["production"]["coal"], 5)
            self.assertEqual(data["production"]["unknown"], 3)

    # Exchange
    @patch.object(Formentera, "get_all")
    def test_fetch_exchange_ES_IB_FO(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES.fetch_exchange("ES-IB-FO", "ES-IB-IZ", self.session)
        self.assertIsNot(data_list, [])
        for data in data_list:
            self.assertEqual(data["sortedZoneKeys"], "ES-IB-FO->ES-IB-IZ")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["netFlow"])
            self.assertEqual(data["netFlow"], -10.0)
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(15046037).astimezone(timezone.utc),
            )

    ### Mallorca
    # Exchange
    @patch.object(Mallorca, "get_all")
    def test_fetch_exchange(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES.fetch_exchange(ZoneKey("ES"), ZoneKey("ES-IB-MA"), self.session)
        self.assertIsNot(data_list, [])
        for data in data_list:
            self.assertEqual(data["sortedZoneKeys"], "ES->ES-IB-MA")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["netFlow"])
            self.assertEqual(data["netFlow"], 50.0)
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(15046037).astimezone(timezone.utc),
            )


if __name__ == "__main__":
    main()
