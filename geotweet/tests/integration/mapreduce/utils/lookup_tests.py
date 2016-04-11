import unittest
import os
from os.path import dirname
import sys

from rtree import index

from . import ROOT as GEOTWEET_DIR  # also adds ROOT to path to import from geotweet
from geotweet.mapreduce.utils.lookup import project, SpatialLookup


TEST_GEOJSON_LOCAL = os.path.join(GEOTWEET_DIR, 'data/geo/us_states102005.geojson')
MAX_COUNT = 100
RESULTS_COUNT = 51
PORTLAND = project((-122.5, 45.5))


def exists(location):
    dat = location + ".dat"
    idx = location + ".idx"
    return os.path.isfile(dat) and os.path.isfile(idx)


def clear(location):
    try: os.remove(location + ".idx")
    except: pass
    try: os.remove(location + ".dat")
    except: pass


class GetObjectTests(unittest.TestCase):
    
    def setUp(self):
        self.src = TEST_GEOJSON_LOCAL
        # remove existing index
        self.lookup = SpatialLookup(src=self.src)
    
    def test_none(self):
        coord = None
        feature = self.lookup.get_object(coord)
        error = "Expected None coordinates to return None"
        self.assertIsNone(feature, error.format(coord))

    def test_invalid_list(self):
        coord = [200, -100, 500]
        feature = self.lookup.get_object(coord)
        error = "Expected invalid coordinates < {0} > to return None"
        self.assertIsNone(feature, error.format(coord))

    def test_valid(self):
        coord = PORTLAND
        expected = 'Oregon'
        prop = 'NAME'
        feature = self.lookup.get_object(coord)
        actual = feature[prop]
        error = "Unexpected value of property < {0} > for given coordinates < {1} >\n"
        error += "Expected: < {2} >, Actual: < {3} >"
        error = error.format(prop, coord, expected, actual)
        self.assertEqual(expected, actual, error)


if __name__ == "__main__":
    unittest.main()
