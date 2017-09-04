import unittest

from parsers import IN_AP


class Test_IN_AP(unittest.TestCase):

    def test_fetch_production(self):
        try:
            data = IN_AP.fetch_production()
            self.assertIsNotNone(data)
        except Exception as ex:
            self.assertIsNotNone(ex)

    def test_fetch_consumption(self):
        try:
            data = IN_AP.fetch_consumption()
            self.assertIsNotNone(data)
        except Exception as ex:
            self.assertIsNotNone(ex)


if __name__ == '__main__':
    unittest.main()
