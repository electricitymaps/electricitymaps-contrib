import unittest

from parsers import ESIOS
from parsers.lib import ParserException


class TestESIOS(unittest.TestCase):

    def test_fetch_exchange(self):
        try:
            ESIOS.fetch_exchange('ES', 'MA')
            self.fail("ParserException is expected")
        except ParserException as ex:
            self.assertIsNotNone(ex)
        except Exception:
            self.fail("Exception isn't expected")

if __name__ == '__main__':
    unittest.main()
