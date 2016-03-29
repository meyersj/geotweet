import unittest
import os
import sys
import subprocess

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.extract import Extractor


class ExtractorTests(unittest.TestCase):

    def setUp(self):
        self.ex = Extractor()
        self.source = os.path.join(root, 'data/osm/rhode-island-latest.osm.pbf')
        self.target = os.path.join(root, 'data/osm/.tmp-rhode-island-latest.osm')

    def clear_tmp(self, tmp):
        try:
            os.remove(tmp)
        except OSError:
            pass
    
    def test_osmosis(self):
        ret = subprocess.call("osmosis -v", shell=True)
        error = "Error checking version of osmosis with `osmosis -v`."
        error += "\n\nIs it `osmosis` installed and on your path?"
        self.assertTrue(ret == 0, error)

    def test_url_valid(self):
        self.clear_tmp(self.target)
        res = self.ex._extract(self.source, self.target)
        error = "Error: Extractor._extract returned False, Source: {0}, Target: {1}"
        self.assertTrue(res, error.format(self.source, self.target))
        error = "Error: output file {0} does not exist".format(self.target)
        self.assertTrue(os.path.isfile(self.target), error)
        self.clear_tmp(self.target)


if __name__ == "__main__":
    unittest.main()
