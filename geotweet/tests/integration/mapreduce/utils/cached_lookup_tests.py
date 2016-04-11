import unittest
import os
from os.path import dirname
import sys

from rtree import index

from . import ROOT as GEOTWEET_DIR  # also adds ROOT to path to import from geotweet
from geotweet.mapreduce.utils.lookup import project
from geotweet.mapreduce.utils.lookup import CachedCountyLookup
from geotweet.mapreduce.utils.lookup import CachedMetroLookup


# live data
GEO_DIR = os.path.join(GEOTWEET_DIR, 'data/geo')
TEST_GEOJSON_LOCAL = os.path.join(GEO_DIR, 'us_states102005.geojson')
METRO_GEOJSON_LOCAL = os.path.join(GEO_DIR, 'us_metro_areas102005.geojson')
COUNTIES_GEOJSON_LOCAL = os.path.join(GEO_DIR, 'us_counties102005.geojson')

# test params
PORTLAND = (-122.5, 45.5)
COUNTY_RESULTS = ('41', '051')
METRO_RESULTS = 'Portland, OR--WA'
METERS_PER_MILE = 1609
METRO_DISTANCE = 50 * METERS_PER_MILE


class CachedCountyTests(unittest.TestCase):

    def setUp(self):
        self.src = COUNTIES_GEOJSON_LOCAL
        self.lookup = CachedCountyLookup(src=self.src)

    def test_lookup(self):
        expected = COUNTY_RESULTS
        found = self.lookup.get(PORTLAND)
        error = "Lookup did not return expected results"
        self.assertEqual(found, expected, error)
        found = self.lookup.get(PORTLAND)
        error = "Lookup did not return cached result"
        self.assertEqual(found, expected, error)


class CachedMetroTests(unittest.TestCase):

    def setUp(self):
        self.src = METRO_GEOJSON_LOCAL
        self.lookup = CachedMetroLookup(src=self.src)

    def test_lookup(self):
        expected = METRO_RESULTS
        found = self.lookup.get(PORTLAND, buffer_size=METRO_DISTANCE)
        error = "Lookup did not return expected results"
        self.assertEqual(found, expected, error)
        found = self.lookup.get(PORTLAND, buffer_size=METRO_DISTANCE)
        error = "Lookup did not return cached result"
        self.assertEqual(found, expected, error)


if __name__ == "__main__":
    unittest.main()
