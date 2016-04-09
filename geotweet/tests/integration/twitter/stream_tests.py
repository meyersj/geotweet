import unittest
import json
import os
from os.path import dirname
import sys

from . import ROOT
from geotweet.twitter.stream import TwitterStream
from geotweet.twitter.steps import ProcessStep


TIMEOUT = 1
BBOX = ["-125.0011,24.9493", "-66.9326,49.5904"]


class StreamTests(unittest.TestCase):

    def setUp(self):
        self.stream = TwitterStream()
        
    def test_stream_no_location(self):
        self.stream.start(ProcessStep(), timeout=TIMEOUT)
         
    def test_stream_location(self):
        self.stream.start(ProcessStep(), timeout=TIMEOUT, locations=BBOX)


if __name__ == "__main__":
    unittest.main()
