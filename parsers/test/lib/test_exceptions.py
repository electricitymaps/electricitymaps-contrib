import unittest

from parsers.lib import ParserException


class TestParserException(unittest.TestCase):

    def test_instance(self):
        exception = ParserException('ESIOS', "Parser exception")
        self.assertIsInstance(exception, ParserException)
        self.assertEquals(str(exception), 'ESIOS Parser: Parser exception')


if __name__ == '__main__':
    unittest.main()
