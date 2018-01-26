import unittest

from arrow import get
from parsers import ES_CN
from mock import patch
from reescraper import Response
from reescraper import ElHierro, GranCanaria, Gomera, LanzaroteFuerteventura, LaPalma, Tenerife


class TestESIB(unittest.TestCase):

    def setUp(self):
        self.session = None

        self.morning = get(1514629800).datetime
        self.afternoon = get(1514644200).datetime
        self.evening = get(1514673000).datetime

    @patch.object(Tenerife, 'get_all')
    @patch.object(LaPalma, 'get_all')
    @patch.object(LanzaroteFuerteventura, 'get_all')
    @patch.object(Gomera, 'get_all')
    @patch.object(GranCanaria, 'get_all')
    @patch.object(ElHierro, 'get_all')
    def test_fetch_consumption(self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene):
        el_hierro.return_value = []
        gran_canaria.return_value = []
        gomera.return_value = []
        lanza_fuerte.return_value = [
            Response(self.morning, 25.0),
            Response(self.afternoon, 200.1),
            Response(self.evening, 28.0)
        ]
        palma.return_value = []
        tene.return_value = []

        data = ES_CN.fetch_consumption('ES-CN-FVLZ', self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for consumption in data:
            self.assertEqual(consumption['countryCode'], 'ES-CN-FVLZ')
            self.assertEqual(consumption['source'], 'demanda.ree.es')
            self.assertIsNotNone(consumption['datetime'])
            self.assertTrue(consumption['datetime'] == self.morning
                            or consumption['datetime'] == self.afternoon
                            or consumption['datetime'] == self.evening)
            if self.morning == consumption['datetime']:
                self.assertEqual(consumption['consumption'], 25.0)
            elif self.afternoon == consumption['datetime']:
                self.assertEqual(consumption['consumption'], 200.1)
            elif self.evening == consumption['datetime']:
                self.assertEqual(consumption['consumption'], 28.0)

    @patch.object(Tenerife, 'get_all')
    @patch.object(LaPalma, 'get_all')
    @patch.object(LanzaroteFuerteventura, 'get_all')
    @patch.object(Gomera, 'get_all')
    @patch.object(GranCanaria, 'get_all')
    @patch.object(ElHierro, 'get_all')
    def test_fetch_production(self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene):
        self.empty_production = get(1514673600).datetime
        el_hierro.return_value = []
        gran_canaria.return_value = []
        gomera.return_value = []
        lanza_fuerte.return_value = [
            Response(self.morning, 25.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 200.1, 182.0, 12.2, 3.1, 0.0, 0.0, 5.3, 0.0),
            Response(self.evening, 28.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        ]
        palma.return_value = []
        tene.return_value = []

        data = ES_CN.fetch_production('ES-CN-FVLZ', self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for production in data:
            self.assertEqual(production['countryCode'], 'ES-CN-FVLZ')
            self.assertEqual(production['source'], 'demanda.ree.es')
            self.assertIsNotNone(production['datetime'])
            self.assertIsNotNone(production['production'])
            self.assertIsNotNone(production['storage'])
            self.assertTrue(production['datetime'] == self.morning
                            or production['datetime'] == self.afternoon
                            or production['datetime'] == self.evening)
            if self.morning == production['datetime']:
                self.assertEqual(production['production']['gas'], 4.5)
                self.assertEqual(production['production']['oil'], 4.0)
                self.assertEqual(production['production']['hydro'], 5.0)
                self.assertEqual(production['production']['solar'], 0.4)
                self.assertEqual(production['production']['wind'], 0.5)
                self.assertEqual(production['storage']['hydro'], 0.0)
            elif self.afternoon == production['datetime']:
                self.assertEqual(production['production']['gas'], 12.2)
                self.assertEqual(production['production']['oil'], 182.0)
                self.assertEqual(production['production']['hydro'], 0.0)
                self.assertEqual(production['production']['solar'], 5.3)
                self.assertEqual(production['production']['wind'], 3.1)
                self.assertEqual(production['storage']['hydro'], 0.0)
            elif self.evening == production['datetime']:
                self.assertEqual(production['production']['gas'], 4.5)
                self.assertEqual(production['production']['oil'], 4.0)
                self.assertEqual(production['production']['hydro'], 5.0)
                self.assertEqual(production['production']['solar'], 0.4)
                self.assertEqual(production['production']['wind'], 0.5)
                self.assertEqual(production['storage']['hydro'], 0.0)


if __name__ == '__main__':
    unittest.main()
