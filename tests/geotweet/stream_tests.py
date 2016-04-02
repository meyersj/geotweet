import unittest
import json
import os
from os.path import dirname
import sys

root = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(root)

from geotweet.stream import TwitterStream


TIMEOUT = 1
BBOX = ["-125.0011,24.9493", "-66.9326,49.5904"]


class MockHandler(object):

    def handle(self, record):
        pass


class StreamTests(unittest.TestCase):

    def setUp(self):
        self.stream = TwitterStream()
        
    def test_stream_no_location(self):
        self.stream.start(MockHandler(), timeout=TIMEOUT)
         
    def test_stream_location(self):
        self.stream.start(MockHandler(), timeout=TIMEOUT, locations=BBOX)


if __name__ == "__main__":
    unittest.main()
