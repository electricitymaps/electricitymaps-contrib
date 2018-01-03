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
        el_hierro.return_value = [
            Response(self.morning, 10.0),
            Response(self.afternoon, 5.6),
            Response(self.evening, 12.0)
        ]

        gran_canaria.return_value = [
            Response(self.morning, 15.0),
            Response(self.afternoon, 443.6),
            Response(self.evening, 18.0)
        ]
        gomera.return_value = [
            Response(self.morning, 5.0),
            Response(self.afternoon, 9.3),
            Response(self.evening, 8.0)
        ]
        lanza_fuerte.return_value = [
            Response(self.morning, 25.0),
            Response(self.afternoon, 200.1),
            Response(self.evening, 28.0)
        ]
        palma.return_value = [
            Response(self.morning, 30.0),
            Response(self.afternoon, 34.7),
            Response(self.evening, 32.0)
        ]
        tene.return_value = [
            Response(self.morning, 20.0),
            Response(self.afternoon, 452.6),
            Response(self.evening, 22.0)
        ]

        data = ES_CN.fetch_consumption('ES-CN', self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for consumption in data:
            self.assertEqual(consumption['countryCode'], 'ES-CN')
            self.assertEqual(consumption['source'], 'demanda.ree.es')
            self.assertIsNotNone(consumption['datetime'])
            self.assertTrue(consumption['datetime'] == self.morning
                            or consumption['datetime'] == self.afternoon
                            or consumption['datetime'] == self.evening)
            if self.morning == consumption['datetime']:
                self.assertEqual(consumption['consumption'], 105.0)
            elif self.afternoon == consumption['datetime']:
                self.assertEqual(consumption['consumption'], 1145.9)
            elif self.evening == consumption['datetime']:
                self.assertEqual(consumption['consumption'], 120.0)

    @patch.object(Tenerife, 'get_all')
    @patch.object(LaPalma, 'get_all')
    @patch.object(LanzaroteFuerteventura, 'get_all')
    @patch.object(Gomera, 'get_all')
    @patch.object(GranCanaria, 'get_all')
    @patch.object(ElHierro, 'get_all')
    def test_fetch_production(self, el_hierro, gran_canaria, gomera, lanza_fuerte, palma, tene):
        self.empty_production = get(1514673600).datetime
        el_hierro.return_value = [
            Response(self.morning, 10.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 5.6, 1.7, 0.0, 1.6, 0.0, 0.0, 0.0, 2.4),
            Response(self.evening, 12.0, 2.0, 2.0, 0.5, 2.5, 2.5, 0.0, 3.0),
            Response(self.empty_production, 12.0, 2.0, 2.0, 0.5, 2.5, 2.5, 0.0, 3.0)
        ]

        gran_canaria.return_value = [
            Response(self.morning, 15.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 443.6, 34.7, 0.0, 33.3, 172.4, 184.5, 17.5, 0.0),
            Response(self.evening, 18.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 2.0, 2.0, 0.5, 2.5, 2.5, 0.0, 3.0)
        ]
        gomera.return_value = [
            Response(self.morning, 5.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 9.3, 9.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            Response(self.evening, 8.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 2.0, 2.0, 0.5, 2.5, 2.5, 0.0, 3.0)
        ]
        lanza_fuerte.return_value = [
            Response(self.morning, 25.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 200.1, 182.0, 12.2, 3.1, 0.0, 0.0, 5.3, 0.0),
            Response(self.evening, 28.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        ]
        palma.return_value = [
            Response(self.morning, 30.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 34.7, 30.2, 0.0, 3.3, 0.0, 0.0, 2.1, 0.0),
            Response(self.evening, 32.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 2.0, 2.0, 0.5, 2.5, 2.5, 0.0, 3.0)
        ]
        tene.return_value = [
            Response(self.morning, 20.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.afternoon, 452.6, 34.9, 0.0, 28.2, 143.8, 179.2, 66.3, 0.0),
            Response(self.evening, 22.0, 1.5, 2.0, 0.5, 2.5, 2.5, 0.4, 5.0),
            Response(self.empty_production, 12.0, 2.0, 2.0, 0.5, 2.5, 2.5, 0.0, 3.0)
        ]

        data = ES_CN.fetch_production('ES-CN', self.session)
        self.assertIsNotNone(data)
        self.assertIs(len(data), 3)
        for production in data:
            self.assertEqual(production['countryCode'], 'ES-CN')
            self.assertEqual(production['source'], 'demanda.ree.es')
            self.assertIsNotNone(production['datetime'])
            self.assertIsNotNone(production['production'])
            self.assertIsNotNone(production['storage'])
            self.assertTrue(production['datetime'] == self.morning
                            or production['datetime'] == self.afternoon
                            or production['datetime'] == self.evening)
            if self.morning == production['datetime']:
                self.assertEqual(production['production']['gas'], 27.0)
                self.assertEqual(production['production']['oil'], 24.0)
                self.assertEqual(production['production']['hydro'], 25.0)
                self.assertEqual(production['production']['solar'], 2.4)
                self.assertEqual(production['production']['wind'], 3.0)
                self.assertEqual(production['storage']['hydro'], -5.0)
            elif self.afternoon == production['datetime']:
                self.assertEqual(production['production']['gas'], 328.4)
                self.assertEqual(production['production']['oil'], 656.5)
                self.assertEqual(production['production']['hydro'], 0.0)
                self.assertEqual(production['production']['solar'], 91.2)
                self.assertEqual(production['production']['wind'], 69.5)
                self.assertEqual(production['storage']['hydro'], -2.4)
            elif self.evening == production['datetime']:
                self.assertEqual(production['production']['gas'], 27.0)
                self.assertEqual(production['production']['oil'], 24.5)
                self.assertEqual(production['production']['hydro'], 25.0)
                self.assertEqual(production['production']['solar'], 2.0)
                self.assertEqual(production['production']['wind'], 3.0)
                self.assertEqual(production['storage']['hydro'], -3.0)


if __name__ == '__main__':
    unittest.main()
