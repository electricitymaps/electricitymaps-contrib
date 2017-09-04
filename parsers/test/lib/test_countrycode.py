import unittest

from parsers.lib import countrycode


class TestCountyCode(unittest.TestCase):

    def test_assert_country_code(self):
        try:
            countrycode.assert_country_code('ES', 'ES')
        except Exception:
            self.fail("assert_country_code() raised Exception unexpectedly!")

        try:
            countrycode.assert_country_code('ES', 'ES-IB')
        except Exception as ex:
            self.assertIsInstance(ex, Exception)


if __name__ == '__main__':
    unittest.main()
