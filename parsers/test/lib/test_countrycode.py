import unittest

from parsers.lib.exceptions import ParserException
from parsers.lib import countrycode


class TestCountyCode(unittest.TestCase):

    def test_assert_zone_key(self):
        try:
            countrycode.assert_zone_key('ES', 'ES', 'ESIOS')
        except ParserException as ex:
            self.fail("assert_zone_key() raised ParserException unexpectedly!")

        try:
            countrycode.assert_zone_key('ES', 'ES-IB')
        except ParserException as ex:
            self.assertIsInstance(ex, ParserException)
            self.assertEqual(str(ex), "ES Parser (ES): zone_key expected ES-IB, is ES")

        try:
            countrycode.assert_zone_key('ES', 'ES-IB', 'ESIOS')
        except ParserException as ex:
            self.assertIsInstance(ex, ParserException)
            self.assertEqual(str(ex), "ESIOS Parser (ES): zone_key expected ES-IB, is ES")


if __name__ == '__main__':
    unittest.main()
