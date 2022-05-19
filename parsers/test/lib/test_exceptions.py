import unittest

from parsers.lib.exceptions import ParserException


class TestParserException(unittest.TestCase):
    def test_instance(self):
        exception = ParserException("ESIOS", "Parser exception")
        self.assertIsInstance(exception, ParserException)
        self.assertEqual(str(exception), "ESIOS Parser: Parser exception")

    def test_instance_with_zone_key(self):
        exception = ParserException("ESIOS", "Parser exception", "ES")
        self.assertIsInstance(exception, ParserException)
        self.assertEqual(str(exception), "ESIOS Parser (ES): Parser exception")


if __name__ == "__main__":
    unittest.main()
