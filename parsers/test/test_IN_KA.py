import unittest

from parsers import IN_KA


class Test_IN_KA(unittest.TestCase):

    def test_get_response(self):
        try:
            data = IN_KA.fetch_production()
            self.assertIsNotNone(data)
        except Exception as ex:
            self.assertIsNotNone(ex)


if __name__ == '__main__':
    unittest.main()
