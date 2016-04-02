import unittest
import json
import os
from os.path import dirname
import sys

root = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(root)

from geotweet.handle import LogTweetHandler, Tweet


TEST_STREAM = os.path.join(root, 'data/testdata/twitter-raw.log')


class HandlerTests(unittest.TestCase):

    def setUp(self):
        self.handler = LogTweetHandler()

    def test_invalid_empty(self):
        data = dict()
        error = "Expected validate_geotweet to return False"
        self.assertFalse(self.handler.validate_geotweet(data), error)
    
    def test_invalid_none(self):
        data = dict(geo=None, user=None)
        error = "Expected validate_geotweet to return False"
        self.assertFalse(self.handler.validate_geotweet(data), error)

    def test_invalid_geo(self):
        data = dict(geo=None, user={'username':'jeff'})
        error = "Expected validate_geotweet to return False"
        self.assertFalse(self.handler.validate_geotweet(data), error)

    def test_valid(self):
        data = dict(geo=[-122.5, 45.5], user={'username':'jeff'})
        error = "Expected validate_geotweet to return True"
        self.assertTrue(self.handler.validate_geotweet(data), error)


class TweetTests(unittest.TestCase):

    def setUp(self):
        self.handler = LogTweetHandler()
        self.tweets = []
        with open(TEST_STREAM, 'r') as f:
            for tweet in f.read().splitlines():
                self.tweets.append(json.loads(tweet))
    
    def test_construction(self):
        for tweet in self.tweets:
            if self.handler.validate_geotweet(tweet):
                t = Tweet(tweet)
                self.assertIsNotNone(t.lonlat, 'Parsed tweet lonlat is None')
                self.assertIsNotNone(t.user_id, 'Parsed tweet user_id is None')


if __name__ == "__main__":
    unittest.main()
