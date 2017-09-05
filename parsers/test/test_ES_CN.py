import unittest

from requests import Session
from parsers import ES_CN
from mock import patch
from reescraper import Response
from reescraper import ElHierro, GranCanaria, Gomera, LanzaroteFuerteventura, LaPalma, Tenerife


class TestESIB(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        response = Response(1504603773)
        response.demand = 1000.0
        response.hydraulic = 50.0
        self.mocked_response = response

    @patch.object(ElHierro, 'get')
    @patch.object(GranCanaria, 'get')
    @patch.object(Gomera, 'get')
    @patch.object(LanzaroteFuerteventura, 'get')
    @patch.object(LaPalma, 'get')
    @patch.object(Tenerife, 'get')
    def test_fetch_consumption(self, el_hierro_get, canaria_get, gomera_get, lanza_get, palma_get, tene_get):
        el_hierro_get.return_value = self.mocked_response
        canaria_get.return_value = self.mocked_response
        gomera_get.return_value = self.mocked_response
        lanza_get.return_value = self.mocked_response
        palma_get.return_value = self.mocked_response
        tene_get.return_value = self.mocked_response

        try:
            data = ES_CN.fetch_consumption('ES-CN', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['countryCode'], 'ES-CN')
            self.assertEqual(data['source'], 'demanda.ree.es')
            self.assertIsNotNone(data['datetime'])
            self.assertEqual(data['consumption'], 6000.0)
        except Exception as ex:
            self.fail(ex.message)

    @patch.object(ElHierro, 'get')
    @patch.object(GranCanaria, 'get')
    @patch.object(Gomera, 'get')
    @patch.object(LanzaroteFuerteventura, 'get')
    @patch.object(LaPalma, 'get')
    @patch.object(Tenerife, 'get')
    def test_fetch_production(self, el_hierro_get, canaria_get, gomera_get, lanza_get, palma_get, tene_get):
        el_hierro_get.return_value = self.mocked_response
        canaria_get.return_value = self.mocked_response
        gomera_get.return_value = self.mocked_response
        lanza_get.return_value = self.mocked_response
        palma_get.return_value = self.mocked_response
        tene_get.return_value = self.mocked_response

        try:
            data = ES_CN.fetch_production('ES-CN', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['countryCode'], 'ES-CN')
            self.assertEqual(data['source'], 'demanda.ree.es')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['production'])
            self.assertEqual(data['production']['hydro'], 250.0)
            self.assertIsNotNone(data['storage'])
            self.assertEqual(data['storage']['hydro'], -50.0)
        except Exception as ex:
            self.fail(ex.message)

if __name__ == '__main__':
    unittest.main()
