import unittest
import warnings

from parsers.lib import web
from parsers.lib.exceptions import ParserException

# Suppress ResourceWarning about unclosed sockets from requests when
# running unittests. This is safe to do, see link below.
# https://github.com/requests/requests/issues/2214


def ignore_resource_warning(test_function):
    def run_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_function(self, *args, **kwargs)

    return run_test


class TestResponses(unittest.TestCase):
    @ignore_resource_warning
    def test_get_response(self):
        try:
            response = web.get_response("ES", "https://www.google.es")
            self.assertIsNotNone(response)
        except ParserException as ex:
            self.fail("assert_zone_key() raised Exception unexpectedly!")

    @ignore_resource_warning
    def test_get_response_text(self):
        try:
            response_text = web.get_response_text("ES", "https://www.google.es")
            self.assertIsNotNone(response_text)
        except ParserException as ex:
            self.fail("assert_zone_key() raised Exception unexpectedly!")

    @ignore_resource_warning
    def test_get_response_soup(self):
        try:
            response_soup = web.get_response_soup("ES", "https://www.google.es")
            self.assertIsNotNone(response_soup)
        except ParserException as ex:
            self.fail("assert_zone_key() raised Exception unexpectedly!")


if __name__ == "__main__":
    unittest.main()
