import unittest
import os
from os.path import dirname
import sys
import json

from rtree import index

from . import ROOT
from geotweet.mapreduce.utils.lookup import project, SpatialLookup


testdata = os.path.join(dirname(os.path.abspath(__file__)), 'testdata')
def read(geojson):
    return json.loads(open(os.path.join(testdata, geojson), 'r').read())


"""
      P53000
    ______
   |      |
   |      |
   |______|  Polygon 2

      P3200
    ______
   |      |
   |  P   |
   |______|  Polygon 2

"""

POLYGON_1 = read('polygon_102500_1.geojson')
POLYGON_2 = read('polygon_102500_2.geojson')
POINT_WITHIN = read('point_within.geojson')
POINT_53000M =  read('point_53000m.geojson')
POINT_3200M =  read('point_3200m.geojson')


def init_polygon_1_index():
    location = SpatialLookup()
    idx = index.Rtree()
    polygon = location._build_obj(POLYGON_1)
    location.data_store[1] = polygon
    idx.insert(1, polygon['geometry'].bounds)
    location.idx = idx
    return location

def init_polygon_2_index():
    location = init_polygon_1_index()
    polygon = location._build_obj(POLYGON_2)
    location.data_store[2] = polygon
    location.idx.insert(2, polygon['geometry'].bounds)
    return location


class GetObjectBasic(unittest.TestCase):
  
    def setUp(self):
        self.location = init_polygon_1_index()

    def assert_found(self, point):
        found = self.location.get_object(point)
        error = "get_object failed to return object"
        self.assertIsNotNone(found, error)
    
    def assert_none(self, point):
        found = self.location.get_object(point)
        error = "get_object should return None: Actual < {0} >".format(found)
        self.assertIsNone(found, error)

    def test_basic(self):
        self.assert_found(project(POINT_WITHIN['geometry']['coordinates']))
        self.assert_none(project(POINT_3200M['geometry']['coordinates']))
        self.assert_none(project(POINT_53000M['geometry']['coordinates']))
    
    def test_buffer_none(self):
        point = project(POINT_3200M['geometry']['coordinates'])
        found = self.location.get_object(point, buffer_size=0)
        self.assertIsNone(found)
    
    def test_buffer_outside_buffer(self):
        point = project(POINT_3200M['geometry']['coordinates'])
        found = self.location.get_object(point, buffer_size=3000)
        self.assertIsNone(found)
    
    def test_buffer_within_buffer(self):
        point = project(POINT_3200M['geometry']['coordinates'])
        found = self.location.get_object(point, buffer_size=4000)
        self.assertIsNotNone(found)


class GetObjectOrder(unittest.TestCase):
  
    def setUp(self):
        self.location = init_polygon_2_index()

    def assert_found(self, point):
        found = self.location.get_object(point)
        error = "get_object failed to return object"
        self.assertIsNotNone(found, error)
    
    def assert_none(self, point):
        found = self.location.get_object(point)
        error = "get_object should return None: Actual < {0} >".format(found)
        self.assertIsNone(found, error)
    
    def test_buffer_nearest1(self):
        point = project(POINT_WITHIN['geometry']['coordinates'])
        found = self.location.get_object(point, buffer_size=100000)
        self.assertIsNotNone(found, "get_object failed to return object")
        error = "get_object failed to return object with id=polygon1: Actual < {0} >"
        self.assertEqual('polygon1', found['id'], error.format(found['id']))

    def test_buffer_nearest2(self):
        point = project(POINT_3200M['geometry']['coordinates'])
        found = self.location.get_object(point, buffer_size=100000)
        self.assertIsNotNone(found, "get_object failed to return object")
        error = "get_object failed to return object with id=polygon1: Actual < {0} >"
        self.assertEqual('polygon1', found['id'], error.format(found['id']))
   

if __name__ == "__main__":
    unittest.main()
