import unittest
import os
from os.path import dirname
import sys

root = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(root)

from geotweet.osm.download import Downloader
from geotweet.osm.download import US_GEOFABRIK


class DownloaderTests(unittest.TestCase):

    def setUp(self):
        self.dl = Downloader()
        self.valid_state = "Rhode Island"
        self.valid_url = US_GEOFABRIK.format("rhode-island")
        self.invalid_url = US_GEOFABRIK.format("rhod-island")

    def clear_tmp(self):
        tmp = self.dl.get_filename(self.valid_url)
        try:
            os.remove(tmp)
        except OSError:
            pass

    def test_url_valid(self):
        state = "Rhode Island"
        actual = self.dl.build_url(self.valid_state)
        expected = self.valid_url 
        error = "Download url built incorrectly, Actual: < {0}> , Expected: < {1} >"
        self.assertEqual(actual, expected, error.format(actual, expected))

    def test_valid_download(self):
        self.clear_tmp() 
        res = self.dl._download(self.valid_url)
        tmp = self.dl.get_filename(self.valid_url)
        error = "File < {0} > was expected to be downloaded. does not exist"
        self.assertTrue(os.path.isfile(tmp), error.format(tmp))
        self.clear_tmp()
    
    def test_invalid_download(self):
        self.clear_tmp() 
        with self.assertRaises(IOError):
            res = self.dl._download(self.invalid_url)
        

if __name__ == "__main__":
    unittest.main()
