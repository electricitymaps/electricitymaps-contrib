import unittest
import requests
import requests_mock

from datetime import datetime
from pytz import timezone

from parsers import CA_SK
from parsers.lib.exceptions import ParserException


class TestCASK(unittest.TestCase):

    def setUp(self):
        self.adapter = requests_mock.Adapter()
        self.session = requests.Session()
        self.session.mount('https://', self.adapter)

    def test_fetch_consumption_passed_target_datetime_raises_NotImplementedError(self):
        past_datetime = datetime(2020, 12, 31, 23, 59, 59)
        self.assertRaises(NotImplementedError, CA_SK.fetch_consumption, target_datetime=past_datetime)

    def test_fetch_consumption_http_response_not_ok_raises_ParserException(self):
        self.adapter.register_uri('GET', CA_SK.CONSUMPTION_URL, text='', status_code=500)
        self.assertRaises(ParserException, CA_SK.fetch_consumption, session=self.session)

    def test_fetch_consumption_successful_maps_system_load_to_consumption(self):
        expected_consumption = 3134
        self.adapter.register_uri('GET', CA_SK.CONSUMPTION_URL, text=str(expected_consumption),
                                  headers={'date': 'Sun, 12 Dec 2021 02:33:09 GMT'})
        consumption = CA_SK.fetch_consumption(session=self.session)
        self.assertEqual(consumption['consumption'], expected_consumption)

    def test_fetch_consumption_successful_maps_response_date_to_datetime(self):
        expected_datetime = datetime(2020, 12, 31, 23, 59, 59).replace(tzinfo=timezone('GMT'))
        self.adapter.register_uri('GET', CA_SK.CONSUMPTION_URL, text='1337',
                                  headers={'date': 'Thu, 31 Dec 2020 23:59:59 GMT'})
        consumption = CA_SK.fetch_consumption(session=self.session)
        self.assertEqual(consumption['datetime'], expected_datetime)


if __name__ == '__main__':
    unittest.main()
