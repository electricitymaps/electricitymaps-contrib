from datetime import datetime, timezone
from unittest import TestCase, main
from unittest.mock import patch

from requests import Session

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ES


class TestES(TestCase):
    def setUp(self):
        self.session = Session()

    ### El Hierro
    # Consumption
    @patch("requests.Response")
    @patch("parsers.ES.Session.get")
    def test_fetch_consumption(self, mocked_session_get, mocked_response):
        mocked_response.ok = True
        mocked_response.text = r'null({"valoresHorariosGeneracion":[{"ts":"2023-09-04 00:55","dem":5.5,"die":3.2,"gas":0.0,"eol":3.0,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-0.5}]}'
        mocked_session_get.return_value = mocked_response
        data_list = ES.fetch_consumption(
            ZoneKey("ES-CN-HI"), self.session, datetime.fromisoformat("2023-09-04")
        )

        # Test "get" function has been called correctly
        self.assertEqual(
            mocked_session_get.call_args[0][0],
            "https://demanda.ree.es/WSvisionaMovilesCanariasRest/resources/demandaGeneracionCanarias?curva=EL_HIERRO5M&fecha=2023-09-04",
        )

        # Test that the data is parsed correctly afterwards
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["zoneKey"], "ES-CN-HI")
        self.assertEqual(data_list[0]["source"], "demanda.ree.es")
        self.assertEqual(data_list[0]["consumption"], 5.5)
        self.assertTrue(isinstance(data_list[0]["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"],
            datetime(2023, 9, 3, 23, 55, tzinfo=timezone.utc),
        )

    ### El Hierro
    # Production
    @patch("requests.Response")
    @patch("parsers.ES.Session.get")
    def test_fetch_production_storage(self, mocked_session_get, mocked_response):
        mocked_response.ok = True
        mocked_response.text = r'null({"valoresHorariosGeneracion":[{"ts":"2023-09-04 00:55","dem":5.5,"die":3.2,"gas":0.0,"eol":3.0,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-0.5}]}'
        mocked_session_get.return_value = mocked_response
        data_list = ES.fetch_production(
            ZoneKey("ES-CN-HI"), self.session, datetime.fromisoformat("2023-09-04")
        )

        # Test "get" function has been called correctly
        self.assertEqual(
            mocked_session_get.call_args[0][0],
            "https://demanda.ree.es/WSvisionaMovilesCanariasRest/resources/demandaGeneracionCanarias?curva=EL_HIERRO5M&fecha=2023-09-04",
        )

        # Test that the data is parsed correctly afterwards
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["zoneKey"], "ES-CN-HI")
        self.assertEqual(data_list[0]["source"], "demanda.ree.es")
        self.assertEqual(
            data_list[0]["production"],
            {
                "oil": 3.2,
                "solar": 0.0,
                "wind": 3.0,
            },
        )
        self.assertEqual(data_list[0]["storage"], {"hydro": 0.5})
        self.assertTrue(isinstance(data_list[0]["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"],
            datetime(2023, 9, 3, 23, 55, tzinfo=timezone.utc),
        )

    # Test for DST change days
    @patch("requests.Response")
    @patch("parsers.ES.Session.get")
    def test_production_DST_CN(self, mocked_session_get, mocked_response):
        mocked_response.ok = True
        mocked_response.text = r'null({"valoresHorariosGeneracion":[{"ts":"2021-10-31 1A:55","dem":4.8,"die":2.8,"gas":0.0,"eol":3.3,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-1.2},{"ts":"2021-10-31 1B:00","dem":4.5,"die":2.5,"gas":0.0,"eol":3.2,"cc":0.0,"vap":0.0,"fot":0.0,"hid":-1.2}]}'
        mocked_session_get.return_value = mocked_response
        data_list = ES.fetch_production(
            ZoneKey("ES-CN-HI"), self.session, datetime.fromisoformat("2021-10-31")
        )

        # Test "get" function has been called correctly
        self.assertEqual(
            mocked_session_get.call_args[0][0],
            "https://demanda.ree.es/WSvisionaMovilesCanariasRest/resources/demandaGeneracionCanarias?curva=EL_HIERRO5M&fecha=2021-10-31",
        )

        # Test that the data is parsed correctly afterwards
        self.assertEqual(len(data_list), 2)
        self.assertTrue(isinstance(data_list[0]["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"].astimezone(timezone.utc),
            datetime(2021, 10, 31, 0, 55, tzinfo=timezone.utc),
        )
        self.assertTrue(isinstance(data_list[1]["datetime"], datetime))
        self.assertEqual(
            data_list[1]["datetime"].astimezone(timezone.utc),
            datetime(2021, 10, 31, 1, 0, tzinfo=timezone.utc),
        )

    ### Menorca
    # Production
    @patch("requests.Response")
    @patch("parsers.ES.Session.get")
    def test_fetch_production(self, mocked_session_get, mocked_response):
        mocked_response.ok = True
        mocked_response.text = r'null({"valoresHorariosGeneracion":[{"ts":"2023-09-02 21:00","dem":85.9,"car":0.0,"die":22.6,"gas":59.3,"cc":0.0,"cb":0.0,"fot":1.1,"tnr":0.0,"trn":0.0,"eol":0.2,"emm":2.7,"emi":-0.0,"otrRen":0.0,"resid":0.0,"genAux":0.0,"cogen":0.0,"eif":-0.0}]}'
        mocked_session_get.return_value = mocked_response
        data_list = ES.fetch_production(
            ZoneKey("ES-IB-ME"), self.session, datetime.fromisoformat("2023-09-03")
        )

        # Test "get" function has been called correctly
        self.assertEqual(
            mocked_session_get.call_args[0][0],
            "https://demanda.ree.es/WSvisionaMovilesBalearesRest/resources/demandaGeneracionBaleares?curva=MENORCA5M&fecha=2023-09-03",
        )

        # Test that the data is parsed correctly afterwards
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["zoneKey"], "ES-IB-ME")
        self.assertEqual(data_list[0]["source"], "demanda.ree.es")
        self.assertEqual(
            data_list[0]["production"],
            {
                "biomass": 0.0,
                "coal": 0.0,
                "gas": 0.0,
                "oil": 81.9,
                "solar": 1.1,
                "unknown": 0.0,
                "wind": 0.2,
            },
        )
        self.assertTrue(isinstance(data_list[0]["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"],
            datetime(2023, 9, 2, 19, 0, tzinfo=timezone.utc),
        )

    ### Mallorca
    # Exchange
    @patch("requests.Response")
    @patch("parsers.ES.Session.get")
    def test_fetch_exchange(self, mocked_session_get, mocked_response):
        mocked_response.ok = True
        mocked_response.text = r'null({"valoresHorariosGeneracion":[{"ts":"2023-09-03 19:05","dem":670.3,"car":0.0,"die":0.0,"gas":0.0,"cc":416.4,"cb":309.8,"fot":19.7,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-20.6,"emi":-91.3,"otrRen":0.0,"resid":34.6,"genAux":0.0,"cogen":1.7,"eif":-0.0}]}'
        mocked_session_get.return_value = mocked_response
        data_list = ES.fetch_exchange(
            ZoneKey("ES"),
            ZoneKey("ES-IB-MA"),
            self.session,
            datetime.fromisoformat("2023-09-03"),
        )

        # Test "get" function has been called correctly
        self.assertEqual(
            mocked_session_get.call_args[0][0],
            "https://demanda.ree.es/WSvisionaMovilesBalearesRest/resources/demandaGeneracionBaleares?curva=MALLORCA5M&fecha=2023-09-03",
        )

        # Test that the data is parsed correctly afterwards
        self.assertEqual(len(data_list), 1)
        self.assertEqual(data_list[0]["sortedZoneKeys"], "ES->ES-IB-MA")
        self.assertEqual(data_list[0]["source"], "demanda.ree.es")
        self.assertIsNotNone(data_list[0]["netFlow"])
        self.assertEqual(data_list[0]["netFlow"], 309.8)
        self.assertTrue(isinstance(data_list[0]["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"],
            datetime(2023, 9, 3, 17, 5, tzinfo=timezone.utc),
        )

    # Test for DST change days
    @patch("requests.Response")
    @patch("parsers.ES.Session.get")
    def test_production_DST_IB(self, mocked_session_get, mocked_response):
        mocked_response.ok = True
        mocked_response.text = r'null({"valoresHorariosGeneracion":[{"ts":"2020-10-25 2A:55","dem":261.3,"car":73.3,"die":0.0,"gas":0.0,"cc":127.1,"cb":100.4,"fot":0.0,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-3.5,"emi":-58.1,"otrRen":0.0,"resid":19.2,"genAux":0.0,"cogen":2.9,"eif":-0.0},{"ts":"2020-10-25 2B:00","dem":261.7,"car":73.3,"die":0.0,"gas":0.0,"cc":128.0,"cb":100.4,"fot":0.0,"tnr":0.0,"trn":0.0,"eol":0.0,"emm":-3.3,"emi":-58.1,"otrRen":0.0,"resid":18.5,"genAux":0.0,"cogen":2.9,"eif":-0.0}]}'
        mocked_session_get.return_value = mocked_response
        data_list = ES.fetch_production(
            ZoneKey("ES-IB-MA"), self.session, datetime.fromisoformat("2020-10-25")
        )

        # Test "get" function has been called correctly
        self.assertEqual(
            mocked_session_get.call_args[0][0],
            "https://demanda.ree.es/WSvisionaMovilesBalearesRest/resources/demandaGeneracionBaleares?curva=MALLORCA5M&fecha=2020-10-25",
        )

        # Test that the data is parsed correctly afterwards
        self.assertEqual(len(data_list), 2)
        self.assertTrue(isinstance(data_list[0]["datetime"], datetime))
        self.assertEqual(
            data_list[0]["datetime"].astimezone(timezone.utc),
            datetime(2020, 10, 25, 0, 55, tzinfo=timezone.utc),
        )
        self.assertTrue(isinstance(data_list[1]["datetime"], datetime))
        self.assertEqual(
            data_list[1]["datetime"].astimezone(timezone.utc),
            datetime(2020, 10, 25, 1, 0, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    main()
