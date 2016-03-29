import unittest
import os
import sys
import json

from mrjob.job import MRJob
import Geohash

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.mapreduce.wordcount.geo import MRGeoWordCount, GEOHASH_PRECISION


INPUT = """{
    "description":"Some Description",
    "text":"one two three",
    "lonlat":[-122.5, 45.4]
}"""


class MapperGeohashTests(unittest.TestCase):

    def setUp(self):
        self.mr = MRGeoWordCount()

    def test_none(self):
        func = self.mr.mapper_geohash(None, None)
        self.assertRaises(StopIteration, func.next)
    
    def test_empty(self):
        func = self.mr.mapper_geohash(None, "")
        self.assertRaises(StopIteration, func.next)
    
    def test_valid(self):
        text = "one two three"
        geohash = 'c20fk2'
        out = self.mr.mapper_geohash(None, INPUT).next()
        error = "Incorrect output key, Expected: {0}, Actual: {1}"
        self.assertEqual(geohash, out[0], error.format(geohash, out[0]))
        error = "Incorrect output value, Expected: {0}, Actual: {1}"
        self.assertEqual(text, out[1], error.format(text, out[1]))


if __name__ == "__main__":
    unittest.main()
