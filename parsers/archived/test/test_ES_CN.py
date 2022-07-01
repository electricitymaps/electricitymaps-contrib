import unittest

from arrow import get
from mock import patch
from ree import (
    ElHierro,
    Gomera,
    GranCanaria,
    LanzaroteFuerteventura,
    LaPalma,
    Response,
    Tenerife,
)

from parsers import ES_CN


class TestESIB(unittest.TestCase):
    def setUp(self):
        self.session = None

        self.morning = get(1514629800).datetime
        self.afternoon = get(1514644200).datetime
        self.evening = get(1514673000).datetime

    @patch.object(Tenerife, "get_all")
    @patch.object(LaPalma, "get_all")
    @patch.object(LanzaroteFuerteventura, "get_all")
    @patch.object(Gomera, "get_all")
    @patch.object(GranCanaria, "get_all")
    @patch.object(ElHierro, "get_all")
    def test_fetch_consumption(
        self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene
    ):
        el_hierro.return_value = []
        gran_canaria.return_value = []
        gomera.return_value = []
        lanza_fuerte.return_value = [
            Response(self.morning, 64.4),
            Response(self.afternoon, 200.1),
            Response(self.evening, 54.4),
        ]
        palma.return_value = []
        tene.return_value = []

        data = ES_CN.fetch_consumption("ES-CN-FVLZ", self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for consumption in data:
            self.assertEqual(consumption["zoneKey"], "ES-CN-FVLZ")
            self.assertEqual(consumption["source"], "demanda.ree.es")
            self.assertIsNotNone(consumption["datetime"])
            self.assertTrue(
                consumption["datetime"] == self.morning
                or consumption["datetime"] == self.afternoon
                or consumption["datetime"] == self.evening
            )
            if self.morning == consumption["datetime"]:
                self.assertEqual(consumption["consumption"], 64.4)
            elif self.afternoon == consumption["datetime"]:
                self.assertEqual(consumption["consumption"], 200.1)
            elif self.evening == consumption["datetime"]:
                self.assertEqual(consumption["consumption"], 54.4)

    @patch.object(Tenerife, "get_all")
    @patch.object(LaPalma, "get_all")
    @patch.object(LanzaroteFuerteventura, "get_all")
    @patch.object(Gomera, "get_all")
    @patch.object(GranCanaria, "get_all")
    @patch.object(ElHierro, "get_all")
    def test_fetch_consumption_el_hierro(
        self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene
    ):
        el_hierro.return_value = [
            Response(self.morning, 10.0),
            Response(self.afternoon, 5.6),
            Response(self.evening, 12.0),
        ]
        gran_canaria.return_value = []
        gomera.return_value = []
        lanza_fuerte.return_value = []
        palma.return_value = []
        tene.return_value = []

        data = ES_CN.fetch_consumption("ES-CN-HI", self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for consumption in data:
            self.assertEqual(consumption["zoneKey"], "ES-CN-HI")
            self.assertEqual(consumption["source"], "demanda.ree.es")
            self.assertIsNotNone(consumption["datetime"])
            self.assertTrue(
                consumption["datetime"] == self.morning
                or consumption["datetime"] == self.afternoon
                or consumption["datetime"] == self.evening
            )
            if self.morning == consumption["datetime"]:
                self.assertEqual(consumption["consumption"], 10.0)
            elif self.afternoon == consumption["datetime"]:
                self.assertEqual(consumption["consumption"], 5.6)
            elif self.evening == consumption["datetime"]:
                self.assertEqual(consumption["consumption"], 12.0)

    @patch.object(Tenerife, "get_all")
    @patch.object(LaPalma, "get_all")
    @patch.object(LanzaroteFuerteventura, "get_all")
    @patch.object(Gomera, "get_all")
    @patch.object(GranCanaria, "get_all")
    @patch.object(ElHierro, "get_all")
    def test_fetch_production(
        self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene
    ):
        self.empty_production = get(1514673600).datetime
        el_hierro.return_value = []
        gran_canaria.return_value = []
        gomera.return_value = []
        lanza_fuerte.return_value = [
            Response(self.morning, 64.4, 1.5, 52.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 200.1, 182.0, 12.2, 3.1, 0.0, 0.0, 5.3, 0.0),
            Response(self.evening, 54.4, 1.5, 42.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ]
        palma.return_value = []
        tene.return_value = []

        data = ES_CN.fetch_production("ES-CN-FVLZ", self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for production in data:
            self.assertEqual(production["zoneKey"], "ES-CN-FVLZ")
            self.assertEqual(production["source"], "demanda.ree.es")
            self.assertIsNotNone(production["datetime"])
            self.assertIsNotNone(production["production"])
            self.assertIsNotNone(production["storage"])
            self.assertTrue(
                production["datetime"] == self.morning
                or production["datetime"] == self.afternoon
                or production["datetime"] == self.evening
            )
            if self.morning == production["datetime"]:
                self.assertEqual(production["production"]["gas"], 0.0)
                self.assertEqual(production["production"]["oil"], 58.5)
                self.assertEqual(production["production"]["hydro"], 5.0)
                self.assertEqual(production["production"]["solar"], 0.4)
                self.assertEqual(production["production"]["wind"], 0.5)
                self.assertEqual(production["storage"]["hydro"], 0.0)
            elif self.afternoon == production["datetime"]:
                self.assertEqual(production["production"]["gas"], 0.0)
                self.assertEqual(production["production"]["oil"], 194.2)
                self.assertEqual(production["production"]["hydro"], 0.0)
                self.assertEqual(production["production"]["solar"], 5.3)
                self.assertEqual(production["production"]["wind"], 3.1)
                self.assertEqual(production["storage"]["hydro"], 0.0)
            elif self.evening == production["datetime"]:
                self.assertEqual(production["production"]["gas"], 0.0)
                self.assertEqual(production["production"]["oil"], 48.5)
                self.assertEqual(production["production"]["hydro"], 5.0)
                self.assertEqual(production["production"]["solar"], 0.4)
                self.assertEqual(production["production"]["wind"], 0.5)
                self.assertEqual(production["storage"]["hydro"], 0.0)

    @patch.object(Tenerife, "get_all")
    @patch.object(LaPalma, "get_all")
    @patch.object(LanzaroteFuerteventura, "get_all")
    @patch.object(Gomera, "get_all")
    @patch.object(GranCanaria, "get_all")
    @patch.object(ElHierro, "get_all")
    def test_fetch_production_el_hierro(
        self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene
    ):
        self.empty_production = get(1514673600).datetime
        el_hierro.return_value = [
            Response(self.morning, 10.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 5.6, 1.7, 0.0, 1.6, 0.0, 0.0, 0.0, 2.4),
            Response(self.evening, 12.0, 0.0, 2.0, 0.5, 2.5, 0.0, 0.0, 3.0),
            Response(self.empty_production, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ]
        gran_canaria.return_value = []
        gomera.return_value = []
        lanza_fuerte.return_value = []
        palma.return_value = []
        tene.return_value = []

        data = ES_CN.fetch_production("ES-CN-HI", self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for production in data:
            self.assertEqual(production["zoneKey"], "ES-CN-HI")
            self.assertEqual(production["source"], "demanda.ree.es")
            self.assertIsNotNone(production["datetime"])
            self.assertIsNotNone(production["production"])
            self.assertIsNotNone(production["storage"])
            self.assertTrue(
                production["datetime"] == self.morning
                or production["datetime"] == self.afternoon
                or production["datetime"] == self.evening
            )
            if self.morning == production["datetime"]:
                self.assertEqual(production["production"]["gas"], 0.0)
                self.assertEqual(production["production"]["oil"], 8.5)
                self.assertEqual(production["production"]["hydro"], 0.0)
                self.assertEqual(production["production"]["solar"], 0.4)
                self.assertEqual(production["production"]["wind"], 0.5)
                self.assertEqual(production["storage"]["hydro"], -5.0)
            elif self.afternoon == production["datetime"]:
                self.assertEqual(production["production"]["gas"], 0.0)
                self.assertEqual(production["production"]["oil"], 1.7)
                self.assertEqual(production["production"]["hydro"], 0.0)
                self.assertEqual(production["production"]["solar"], 0.0)
                self.assertEqual(production["production"]["wind"], 1.6)
                self.assertEqual(production["storage"]["hydro"], -2.4)
            elif self.evening == production["datetime"]:
                self.assertEqual(production["production"]["gas"], 0.0)
                self.assertEqual(production["production"]["oil"], 4.5)
                self.assertEqual(production["production"]["hydro"], 0.0)
                self.assertEqual(production["production"]["solar"], 0.0)
                self.assertEqual(production["production"]["wind"], 0.5)
                self.assertEqual(production["storage"]["hydro"], -3.0)


if __name__ == "__main__":
    unittest.main()
