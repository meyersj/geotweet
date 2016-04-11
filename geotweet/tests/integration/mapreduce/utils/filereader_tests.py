import unittest
import os
from os.path import dirname
import sys
from urllib2 import HTTPError
import json

from . import ROOT as GEOTWEET_DIR
from geotweet.mapreduce.utils.reader import FileReader
from geotweet.mapreduce.utils.words import STOPWORDS_LIST_URL


STOPWORDS_LIST_LOCAL = os.path.join(GEOTWEET_DIR, 'data/stopwords.txt')
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
METRO_GEOJSON = os.path.join(AWS_BUCKET, "geotweet/us_metro_areas102005.geojson")


class ReadTests(unittest.TestCase):
    
    def setUp(self):
        pass
        self.valid_remote = STOPWORDS_LIST_URL
        self.valid_local = STOPWORDS_LIST_LOCAL
        self.invalid_local = '/tmp/102948102984109248'
        self.invalid_remote = 'http://google.com/102481092841412'
        self.fr = FileReader()
    
    def test_valid_remote(self):
        self.valid_runner(self.valid_remote)
    
    def test_valid_local(self):
        self.valid_runner(self.valid_local)

    def valid_runner(self, src):
        retrieved = self.fr.read(src) 
        error = "Failed to open file < {0} >".format(src)
        self.assertIsNotNone(retrieved, error)
    
    def test_invalid_remote(self):
        src = self.invalid_remote
        with self.assertRaises(HTTPError):
            retrieved = self.fr.read(src) 

    def test_invalid_local(self):
        src = self.invalid_local
        with self.assertRaises(ValueError):
            retrieved = self.fr.read(src) 

    def test_aws_remote(self):
        text = self.fr.read(METRO_GEOJSON)
        self.assertIsNotNone(text, "Failed to open {0}".format(METRO_GEOJSON))
        self.assertIsNotNone(json.loads(text)['type'], "type field not in data")


if __name__ == "__main__":
    unittest.main()
