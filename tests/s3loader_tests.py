import unittest
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.load import S3Loader


class S3LoaderTests(unittest.TestCase):

    def setUp(self):
        self.ld = S3Loader()

    def clear_tmp(self, tmp):
        try:
            os.remove(tmp)
        except OSError:
            pass
    
    def test_environment_variables(self):
        try:
            self.ld.valid()
        except EnvironmentError as e:
            error = "You must set the following environment variables for S3:\n\n\t"
            error += "\n\t".join(self.ld.envvars) + "\n"
            self.assertTrue(False, error) 

if __name__ == "__main__":
    unittest.main()
