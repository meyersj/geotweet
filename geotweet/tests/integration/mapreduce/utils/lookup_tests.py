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


class BuildTests(unittest.TestCase):

    def setUp(self):
        self.src = TEST_GEOJSON_LOCAL
        self.lookup = SpatialLookup()
        # remove existing index
        self.location = self.lookup.get_location(self.src)
        clear(self.location)
        # build RTree index at `location` 
        self.lookup._build_from_geojson(self.src, self.location)

    def tearDown(self):
        """ clean up """
        clear(self.location)

    def test_build_basic(self):
        # verify it exists
        error = "RTree Index at < {0} > for input < {1} > does not exists."
        error = error.format(self.location, self.src)
        self.assertTrue(exists(self.location), error)

    def test_build_verify_result_count(self):
        coord = PORTLAND
        results_count = RESULTS_COUNT
        assert exists(self.location)
        idx = index.Rtree(self.location)
        features = idx.nearest(coord, num_results=MAX_COUNT, objects=True)
        count = 0
        for i, x in enumerate(features):
            count = i
        error = "Expected count of indexed states to equal states in < {0} >\n"
        error += "Expected: < {1} >, Actual: < {2} >"
        error = error.format(self.src, count, results_count)
        self.assertEqual(count, results_count, error)

    def test_build_verify_lookup(self):
        coord = PORTLAND
        state = 'Oregon'
        prop = 'NAME'
        assert exists(self.location)
        idx = index.Rtree(self.location)
        features = idx.intersection(coord, objects=True)
        try:
            feature = features.next()
        except StopIteration:
            error = "No features returned from index of < {0} >".format(self.src)
            raise Exception(error)
        actual = feature.object['properties'][prop]
        error = "Unexpected name of State for given coordinates < {0} >\n"
        error += "Expected: < {1} >, Actual: < {2} >"
        error = error.format(coord, state, actual)
        self.assertEqual(state, actual, error)


class GetLocationTests(unittest.TestCase):
    
    def setUp(self):
        self.lookup = SpatialLookup()
   
    def test_get_location_none(self):
        src = None
        location = self.lookup.get_location(src)
        error = "None input should return None. Actual < {0} >"
        self.assertIsNone(location, error.format(location))
    
    def test_get_location_empty(self):
        src = ''
        location = self.lookup.get_location(src)
        error = "Empty input should return None. Actual < {0} >"
        self.assertIsNone(location, error.format(location))
    
    def test_get_location_empty(self):
        src = 5
        location = self.lookup.get_location(src)
        error = "Number input < {0} > should return None. Actual < {0} >"
        self.assertIsNone(location, error.format(src, location))

    def test_get_location_path(self):
        src = '/tmp/something.geojson'
        expected = "/tmp/geotweet-rtree-ef0271c8b2f5a84fc06d867058586cb2"
        actual = self.lookup.get_location(src)
        error = "Error converting input to output hashed filename.\n"
        error += "Expected: < {0} >, Actual: < {1} >"
        self.assertEqual(expected, actual, error.format(expected, actual))


class GetObjectTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.src = TEST_GEOJSON_LOCAL
        # remove existing index
        cls.location = SpatialLookup().get_location(cls.src)
        clear(cls.location)
        cls.lookup = SpatialLookup(src=cls.src)
    
    @classmethod
    def tearDownClass(cls):
        clear(cls.location)
    
    def test_none(self):
        coord = None
        assert exists(self.location)
        feature = self.lookup.get_object(coord)
        error = "Expected None coordinates to return None"
        self.assertIsNone(feature, error.format(coord))

    def test_invalid_list(self):
        coord = [200, -100, 500]
        assert exists(self.location)
        feature = self.lookup.get_object(coord)
        error = "Expected invalid coordinates < {0} > to return None"
        self.assertIsNone(feature, error.format(coord))

    def test_valid(self):
        coord = PORTLAND
        expected = 'Oregon'
        prop = 'NAME'
        assert exists(self.location)
        feature = self.lookup.get_object(coord)
        actual = feature[prop]
        error = "Unexpected value of property < {0} > for given coordinates < {1} >\n"
        error += "Expected: < {2} >, Actual: < {3} >"
        error = error.format(prop, coord, expected, actual)
        self.assertEqual(expected, actual, error)


if __name__ == "__main__":
    unittest.main()
