import unittest
import os
from os.path import dirname
import sys
from urllib2 import HTTPError

root = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(root)

from geotweet.mapreduce.wordcount.geo import MRGeoWordCount, GEOHASH_PRECISION
from geotweet.mapreduce.wordcount.geo import SpatialLookup, RTREE_LOCATION


GEOTWEET_DIR = root
STATES_GEOJSON_LOCAL = os.path.join(GEOTWEET_DIR, 'data/geo/us_states.json') 


class SpatialLookupTestCases(unittest.TestCase):

    
    def setUp(self):
        self.valid_local = STATES_GEOJSON_LOCAL
        self.helper = SpatialLookup()

    def clear(self, location):
        try: os.remove(location + ".idx")
        except: pass
        try: os.remove(location + ".dat")
        except: pass

    def test_valid_local(self):
        self.valid_runner(self.valid_local)

    def test_valid_local_invalid_location(self):
        location = self.helper.get_location(self.valid_local)    
        self.clear(location)
        lookup = SpatialLookup(src=self.valid_local)
        invalid_loc = [45.5, -122.5]
        prop = lookup.get_object(invalid_loc)
        self.assertIsNone(prop, "Expected properties for invalid location to be empty")
        self.clear(location)
    
    def valid_runner(self, src):
        location = self.helper.get_location(src)    
        self.clear(location)
        lookup = SpatialLookup(src=src)
        expected = location + ".idx"
        error = "Expected file < {0} > to exist"
        self.assertTrue(os.path.isfile(expected), error.format(expected)) 
        expected = location + ".dat"
        self.assertTrue(os.path.isfile(expected), error.format(expected)) 
        self.validate(lookup)
        self.clear(location)

    def validate(self, lookup):
        portland = [-122.5, 45.5]
        expected = 'Oregon'
        prop = lookup.get_object(portland)
        error = "Lookup of < {0} > failed. Expected < {1} >, Actual < {2} >"
        actual = prop['NAME']
        self.assertEqual(expected, actual, error.format(portland, expected, actual))


if __name__ == "__main__":
    unittest.main()
