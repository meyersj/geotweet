import unittest
import os
from os.path import dirname
import sys
import json

from mrjob.job import MRJob
import Geohash

root = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(root)

GEOTWEET_DIR = root
COUNTIES_GEOJSON_LOCAL = os.path.join(GEOTWEET_DIR, 'data/geo/us_counties.json')
os.environ['COUNTIES_GEOJSON_LOCAL'] = COUNTIES_GEOJSON_LOCAL

from mapreduce.wordcount.geo import MRGeoWordCount, GEOHASH_PRECISION


def build_input(text, desc="My Account", lonlat=[-122.5, 45.4]):
    return json.dumps(dict(
        description=desc,
        text=text,
        lonlat=lonlat
    ))


class MapperTweetTests(unittest.TestCase):

    def setUp(self):
        self.mr = MRGeoWordCount()
        self.mr.mapper_init()

    def test_valid_1(self):
        text = "Foobar Foobaz"
        out_words = ["foobar", "foobaz"]
        tweet = build_input(text)
        self.check_output((None, tweet), out_words)
    
    def test_valid_2(self):
        text = "#Foobar Foobaz (random!!) Galaxy??"
        out_words = ["foobar", "foobaz", "random", "galaxy"]
        tweet = build_input(text)
        self.check_output((None, tweet), out_words)
   
    def check_output(self, src, accept_words):
        try:
            mapper = self.mr.mapper(*src)
            while True:
                output = mapper.next()
                exists = any(output[0].startswith(word) for word in accept_words)
                error = "Unexpected output tuple < {0} >"
                self.assertTrue(exists, error.format(output))
        except StopIteration:
            pass


if __name__ == "__main__":
    unittest.main()
