import unittest
import os
from os.path import dirname
import sys
from urllib2 import HTTPError

root = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(root)

from mapreduce.geo import FileReader, STOPWORDS_LIST_URL


GEOTWEET_DIR = root
STOPWORDS_LIST_LOCAL = os.path.join(GEOTWEET_DIR, 'data/stopwords.txt')


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


if __name__ == "__main__":
    unittest.main()
