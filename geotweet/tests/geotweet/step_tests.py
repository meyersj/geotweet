import unittest
import json
import os
from os.path import dirname
import sys
import inspect

from geotweet.twitter.steps import GeoFilterStep, ExtractStep, LogStep


import geotweet
root = os.path.dirname(inspect.getfile(geotweet))
TEST_STREAM = os.path.join(root, 'data/twitter-api-stream-raw.log')


class GeoFilterStepTests(unittest.TestCase):

    def setUp(self):
        self.step = GeoFilterStep()

    def test_invalid_empty(self):
        data = dict()
        error = "Expected validate_geotweet to return False"
        self.assertFalse(self.step.validate_geotweet(data), error)
    
    def test_invalid_none(self):
        data = dict(coordinates=None, user=None)
        error = "Expected validate_geotweet to return False"
        self.assertFalse(self.step.validate_geotweet(data), error)

    def test_invalid_geo(self):
        data = dict(coordinates=None, user={'username':'jeff'})
        error = "Expected validate_geotweet to return False"
        self.assertFalse(self.step.validate_geotweet(data), error)

    def test_valid(self):
        data = dict(coordinates=[-122.5, 45.5], user={'username':'jeff'})
        error = "Expected validate_geotweet to return True"
        self.assertTrue(self.step.validate_geotweet(data), error)


class ExtractStepTests(unittest.TestCase):

    def setUp(self):
        self.step = ExtractStep()
        self.tweets = []
        with open(TEST_STREAM, 'r') as f:
            for tweet in f.read().splitlines():
                self.tweets.append(json.loads(tweet))
    
    def test_extract(self):
        for tweet in self.tweets:
            if 'coordinates' in tweet and tweet['coordinates']:
                data = self.step.process(tweet)
                self.assertIsNotNone(data['lonlat'], 'Parsed tweet lonlat is None')
                self.assertIsNotNone(data['user_id'], 'Parsed tweet user_id is None')


if __name__ == "__main__":
    unittest.main()
