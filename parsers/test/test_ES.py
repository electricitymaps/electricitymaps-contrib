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

        first_request = Response(1687192328)
        first_request.link["pe_ma"] = 50
        first_request.link["ib_fo"] = 10

        second_request = Response(1687192357)
        second_request.link["pe_ma"] = 50
        second_request.link["ib_fo"] = 10

        self.mocked_responses = [first_request, second_request]

    ### El Hierro
    # Consumption
    @patch.object(ElHierro, "get_all")
    def test_fetch_consumption(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES.fetch_consumption(ZoneKey("ES-CN-HI"), self.session)
        self.assertEqual(len(data_list), 2)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-CN-HI")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertIsNotNone(data["consumption"])
        self.assertEqual(
            data_list[0]["datetime"],
            datetime.fromtimestamp(1687192328).astimezone(timezone.utc),
        )

    # Production
    @patch.object(ElHierro, "get_all")
    def test_fetch_production_el_hierro(self, mocked_get_all):
        mocked_get_all.return_value = [
            Response(1687192328, 10.0, 10, 5, 13, 3, 4, 3.5, 10, 5, 0, 3),
        ]
        data_list = ES.fetch_production(ZoneKey("ES-CN-HI"), self.session)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-CN-HI")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertIsNotNone(data["production"])
            self.assertIsNotNone(data["storage"])
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(1687192328).replace(tzinfo=timezone.utc),
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
        mocked_get_all.return_value = [
            Response(
                timestamp=1687192328,
                demand=10.0,
                diesel=0,
                gas=5,
                wind=13,
                combined=3,
                vapor=4,
                solar=3.5,
                hydraulic=10,
                carbon=5,
                other=3,
            ),
            Response(
                timestamp=1687192328,
                demand=10.0,
                diesel=-10,  # Test negative value
                gas=5,
                wind=13,
                combined=3,
                vapor=4,
                solar=3.5,
                hydraulic=10,
                carbon=5,
                other=3,
            ),
        ]
        data_list = ES.fetch_production(ZoneKey("ES-IB-FO"), self.session)
        self.assertEqual(len(data_list), 2)
        for data in data_list:
            self.assertEqual(data["zoneKey"], "ES-IB-FO")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertTrue(isinstance(data["datetime"], datetime))
            self.assertIsNot(data["production"], {})
            self.assertEqual(
                data["datetime"],
                datetime.utcfromtimestamp(1687192328).replace(tzinfo=timezone.utc),
            )
            self.assertEqual(data["production"]["gas"], 8)
            self.assertEqual(data["production"]["oil"], 4)
            self.assertEqual(data["production"]["hydro"], 10)
            self.assertEqual(data["production"]["solar"], 3.5)
            self.assertEqual(data["production"]["wind"], 13)
            self.assertEqual(data["production"]["coal"], 5)
            self.assertEqual(data["production"]["unknown"], 3)

    # Exchange
    @patch.object(Formentera, "get_all")
    def test_fetch_exchange_ES_IB_FO(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES.fetch_exchange(
            ZoneKey("ES-IB-FO"), ZoneKey("ES-IB-IZ"), self.session
        )
        self.assertEqual(len(data_list), 2)
        for data in data_list:
            self.assertEqual(data["sortedZoneKeys"], "ES-IB-FO->ES-IB-IZ")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["netFlow"])
            self.assertEqual(data["netFlow"], -10.0)
            self.assertTrue(isinstance(data["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"],
            datetime.utcfromtimestamp(1687192328).replace(tzinfo=timezone.utc),
        )

    ### Mallorca
    # Exchange
    @patch.object(Mallorca, "get_all")
    def test_fetch_exchange(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        data_list = ES.fetch_exchange(ZoneKey("ES"), ZoneKey("ES-IB-MA"), self.session)
        self.assertEqual(len(data_list), 2)
        for data in data_list:
            self.assertEqual(data["sortedZoneKeys"], "ES->ES-IB-MA")
            self.assertEqual(data["source"], "demanda.ree.es")
            self.assertIsNotNone(data["netFlow"])
            self.assertEqual(data["netFlow"], 50.0)
            self.assertTrue(isinstance(data["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"],
            datetime.utcfromtimestamp(1687192328).replace(tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    main()
