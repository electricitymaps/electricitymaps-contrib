import unittest

from parsers.lib.exceptions import ParserException
from parsers.lib import web


class TestResponses(unittest.TestCase):

    def test_get_response(self):
        try:
            response = web.get_response('ES', 'https://www.google.es')
            self.assertIsNotNone(response)
        except ParserException as ex:
            self.fail("assert_country_code() raised Exception unexpectedly!")

    def test_get_response_text(self):
        try:
            response_text = web.get_response_text('ES', 'https://www.google.es')
            self.assertIsNotNone(response_text)
        except ParserException as ex:
            self.fail("assert_country_code() raised Exception unexpectedly!")

    def test_get_response_soup(self):
        try:
            response_soup = web.get_response_soup('ES', 'https://www.google.es')
            self.assertIsNotNone(response_soup)
        except ParserException as ex:
            self.fail("assert_country_code() raised Exception unexpectedly!")


if __name__ == '__main__':
    unittest.main()
