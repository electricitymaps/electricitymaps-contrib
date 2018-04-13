import json
import unittest


class ZonesJsonTestcase(unittest.TestCase):
    def setUp(self):
        with open('config/zones.json') as zc:
            self.zones_config = json.load(zc)

    def test_bounding_boxes(self):
        for zone, values in self.zones_config.items():
            bbox = values.get('bounding_box')
            if bbox:
                self.assertLess(bbox[0][0], bbox[1][0])
                self.assertLess(bbox[0][1], bbox[1][1])


if __name__ == '__main__':
    unittest.main(buffer=True)
