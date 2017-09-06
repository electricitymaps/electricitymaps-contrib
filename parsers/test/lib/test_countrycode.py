import unittest

from parsers.lib.exceptions import ParserException
from parsers.lib import countrycode


class TestCountyCode(unittest.TestCase):

    def test_assert_country_code(self):
        try:
            countrycode.assert_country_code('ES', 'ES', 'ESIOS')
        except ParserException as ex:
            self.fail("assert_country_code() raised ParserException unexpectedly!")

        try:
            countrycode.assert_country_code('ES', 'ES-IB')
        except ParserException as ex:
            self.assertIsInstance(ex, ParserException)
            self.assertEquals(str(ex), "ES Parser (ES): Country_code expected ES-IB, is ES")

        try:
            countrycode.assert_country_code('ES', 'ES-IB', 'ESIOS')
        except ParserException as ex:
            self.assertIsInstance(ex, ParserException)
            self.assertEquals(str(ex), "ESIOS Parser (ES): Country_code expected ES-IB, is ES")


if __name__ == '__main__':
    unittest.main()
