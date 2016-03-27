import unittest
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.mongo import MongoGeo, MongoQuery


MONGODB_URI = os.getenv('GEOTWEET_MONGODB_URI', 'mongodb://127.0.0.1:27017')
PORTLAND = [-122.675983, 45.524764]
PROVIDENCE = [-71.404823, 41.827730]
JOHN_HAY = "John Hay Library"


class BoundaryQueryTests(unittest.TestCase):

    def setUp(self):
        self.db = "boundary"

    def connect(self):
        return MongoQuery(db=self.db, collection=self.collection, uri=MONGODB_URI)
    
    def check_field(self, expected, actual, error):
        error = error.format(expected, actual)
        self.assertEqual(expected, actual, error)

    def test_portland_states(self):
        self.collection = "states"
        self.mongo = self.connect()
        query = self.mongo.intersects(PORTLAND)
        
        state = self.mongo.find(query=query).next()
        error = 'STATE is was expected to be : {0}, actual: {1}'
        actual = state['properties']['STATE']
        self.check_field('41', actual, error)
        
        error = 'NAME is was expected to be : {0}, actual: {1}'
        actual = state['properties']['NAME']
        self.check_field('Oregon', actual, error)

    def test_portland_counties(self):
        self.collection = "counties"
        self.mongo = self.connect()
        query = self.mongo.intersects(PORTLAND)
        county = self.mongo.find(query=query).next()
        
        error = 'STATE is was expected to be : {0}, actual: {1}'
        actual = county['properties']['STATE']
        self.check_field('41', actual, error)
       
        error = 'NAME is was expected to be : {0}, actual: {1}'
        actual = county['properties']['NAME']
        self.check_field('Multnomah', actual, error)


class OSMQueryTests(unittest.TestCase):

    def setUp(self):
        self.db = "osm"

    def connect(self):
        return MongoQuery(db=self.db, collection=self.collection, uri=MONGODB_URI)
    
    def check_field(self, expected, actual, error):
        error = error.format(expected, actual)
        self.assertEqual(expected, actual, error)

    def test_rhode_island_poi(self):
        self.collection = "poi"
        self.mongo = self.connect()
        query = self.mongo.near(PROVIDENCE, 150)
        match = False
        for poi in self.mongo.find(query=query):
            if poi['properties']['name'] == JOHN_HAY:
                match = True
                break
        self.assertTrue(match, "No POI matching {0}".format(JOHN_HAY))


if __name__ == "__main__":
    unittest.main()
