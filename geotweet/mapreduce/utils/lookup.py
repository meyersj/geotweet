import sys
import os
import hashlib
import json
import logging

import Geohash
import shapely
from shapely.geometry import shape
from shapely.geometry.point import Point
from rtree import index
from reader import FileReader

from .proj import project, rproject


# reference files to be downloaded from S3 once and stored locally
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
COUNTIES_GEOJSON = os.path.join(AWS_BUCKET, "geotweet/us_counties102005.geojson")
METRO_GEOJSON = os.path.join(AWS_BUCKET, "geotweet/us_metro_areas102005.geojson")
# use local files instead if these environment variables are set with a filepath
if 'COUNTIES_GEOJSON_LOCAL' in os.environ:
    COUNTIES_GEOJSON = os.environ['COUNTIES_GEOJSON_LOCAL']
if 'METRO_GEOJSON_LOCAL' in os.environ:
    METRO_GEOJSON = os.environ['METRO_GEOJSON_LOCAL']


class SpatialLookup(FileReader):
    """ Create a indexed spatial lookup of a geojson file """
    
    idx = None
    data_store = {}

    def __init__(self, src=None):
        if src:
            if not self.is_valid_src(src):
                error = "Arg src=< {0} > is invalid."
                error += " Must be existing file or valid url that starts with 'http'"
                raise ValueError(error.format(src))
            # build index from geojson
            self.data_store, self.idx = self._build_from_geojson(src)
        else:
            # create empty index in memory
            self.data_store, self.idx = self._initialize()

    def _get_nearest(self, point, geom):
        nearest = None
        for bbox_match in self.idx.intersection(geom.bounds):
            # check actual geometry after matching bounding box
            #record = bbox_match.object
            record = self.data_store[bbox_match]
            try:
                if not record['geometry'].intersects(geom):
                    # skip processing current matching bbox
                    continue
                # save only nearest record
                dist = point.distance(record['geometry'])
                if not nearest or dist < nearest['dist']:
                    nearest = dict(data=record, dist=dist)
            except shapely.geos.TopologicalError as e:
                # geometry is invalid so stop processing
                pass
        if nearest:
            return nearest['data']['properties']
        return None

    def _get_all_near(self, geom):
        results = []
        for bbox_match in self.idx.intersection(geom.bounds):
            # check actual geometry after matching bounding box
            #record = bbox_match.object
            record = self.data_store[bbox_match]
            try:
                if not record['geometry'].intersects(geom):
                    # skip processing current matching bbox
                    continue
                # return all intersecting records
                results.append(record['properties'])
            except shapely.geos.TopologicalError as e:
                # geometry is invalid so stop processing
                pass
        return results

    def get_object(self, point, buffer_size=0, multiple=False):
        """ lookup object based on point as [longitude, latitude] """
        # first search bounding boxes
        # idx.intersection method modifies input if it is a list
        try:
            tmp = tuple(point)
        except TypeError:
            return None
        # point must be in the form (minx, miny, maxx, maxy) or (x, y)
        if len(tmp) not in [2, 4]:
            return None

        # buffer point if size is specified
        geom = tmp = Point(tmp)
        if buffer_size:
            geom = tmp.buffer(buffer_size)
        if multiple:
            return self._get_all_near(geom)
        return self._get_nearest(tmp, geom)

    def _build_obj(self, feature):
        feature['geometry'] = shape(feature['geometry'])
        return feature

    def _build_from_geojson(self, src):
        """ Build a RTree index to disk using bounding box of each feature """
        geojson = json.loads(self.read(src))
        idx = index.Index()
        data_store = {}
        for i, feature in enumerate(geojson['features']):
            feature = self._build_obj(feature)
            idx.insert(i, feature['geometry'].bounds)
            data_store[i] = feature
        return data_store, idx

    def _initialize(self):
        """ Build a RTree in memory for features to be added to """
        return {}, index.Index()

    def insert(self, key, feature):
        feature = self._build_obj(feature)
        self.data_store[key] = feature
        self.idx.insert(key, feature['geometry'].bounds)


class CachedLookup(SpatialLookup):
    """ Dowload counties geojson, build index and provide lookup functionality """

    geohash_cache = {}

    def __init__(self, precision=7,  *args, **kwargs):
        super(CachedLookup, self).__init__(*args, **kwargs)
        self.precision = precision
        self.hit = 0
        self.miss = 0

    def get(self, point, buffer_size=0, multiple=False):
        """ lookup state and county based on geohash of coordinates from tweet """
        geohash = Geohash.encode(*point, precision=self.precision)
        key = (geohash, buffer_size, multiple)
        if key in self.geohash_cache:
            # cache hit on geohash
            self.hit += 1
            #print self.hit, self.miss
            return self.geohash_cache[key]
        self.miss += 1
        # cache miss on geohash
        # project point to ESRI:102005
        proj_point = project(point)
        args = dict(buffer_size=buffer_size, multiple=multiple)
        payload = self.get_object(proj_point, **args)
        self.geohash_cache[key] = payload
        return payload


class CachedCountyLookup(CachedLookup):
    """ Dowload counties geojson, build index and provide lookup functionality """

    def __init__(self, src=COUNTIES_GEOJSON, **kwargs):
        super(CachedCountyLookup, self).__init__(src=src, **kwargs)

    def get(self, point):
        payload = super(CachedCountyLookup, self).get(point)
        if payload:
            return payload['STATE'], payload['COUNTY']
        return None, None


class CachedMetroLookup(CachedLookup):
    """ Dowload metro areas geojson, build index and provide lookup functionality """

    def __init__(self, src=METRO_GEOJSON, **kwargs):
        super(CachedMetroLookup, self).__init__(src=src, **kwargs)

    def get(self, point, buffer_size):
        payload = super(CachedMetroLookup, self).get(point, buffer_size=buffer_size)
        if payload:
            return payload['NAME10']
        return None
