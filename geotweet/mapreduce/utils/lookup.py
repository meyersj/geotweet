import sys
import os
import hashlib
import json

import Geohash
import shapely
from shapely.geometry import shape
from shapely.geometry.point import Point
from rtree import index

from reader import FileReader


RTREE_LOCATION = '/tmp/geotweet-rtree-{0}'
# Reference files to be downloaded from S3
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
COUNTIES_GEOJSON_URL = os.path.join(AWS_BUCKET, "geotweet/us_counties.json")
# use local files if these environment variables are set with a filepath
try:
    COUNTIES_GEOJSON = os.environ['COUNTIES_GEOJSON_LOCAL']
except KeyError:
    COUNTIES_GEOJSON = COUNTIES_GEOJSON_URL


class SpatialLookup(FileReader):
    """ Create a indexed spatial lookup of a geojson file """
    
    idx = None

    def __init__(self, src=None):
        if src:
            if not self.is_valid_src(src):
                error = "Arg src=< {0} > is invalid."
                error += " Must be existing file or url that starts with 'http'"
                raise ValueError(error.format(src))
            # location of index based on hash on input src name
            location = self.get_location(src)
            if not self._exists(location):
                # index does not create so fetch data and build it
                self._build(src, location)
            else:
                # index already exists
                self.idx = index.Rtree(location)
    
    def get_location(self, src):
        digest = self.digest(src)
        if not digest:
            return None
        return RTREE_LOCATION.format(digest)

    def digest(self, src):
        if not src or type(src) != str:
            return None
        m = hashlib.md5()
        if self.is_url(src):
            m.update(src)
        else:
            m.update(os.path.abspath(src))
        return m.hexdigest()

    def _exists(self, location):
        dat = location + ".dat"
        idx = location + ".idx"
        if os.path.isfile(dat) and os.path.isfile(idx):
            return True
        return False

    def get_object(self, point):
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
        for bbox_match in self.idx.intersection(tmp, objects=True):
            # check actual geometry
            record = bbox_match.object
            if record['geometry'].intersects(Point(tmp)):
                return record['properties']
        return None
   
    def _build(self, src, location):
        """ Build a RTree index to disk using bounding box of each feature """
        geojson = json.loads(self.read(src))
        def generate():
            for i, feature in enumerate(geojson['features']):
                feature['geometry'] = shape(feature['geometry'])
                yield i, feature['geometry'].bounds, feature
        if geojson:
            # create index, flush to disk which disables access then re-enable access
            self.idx = index.Rtree(location, generate())
            self.idx.close()
            self.idx = index.Rtree(location)


class CachedCountyLookup(SpatialLookup):
    """ Dowload counties geojson, build index and provide lookup functionality """

    geohash_cache = {}

    def __init__(self, src=COUNTIES_GEOJSON):
        super(CachedCountyLookup, self).__init__(src=src)

    def get(self, geohash):
        """ lookup state and county based on geohash of coordinates from tweet """
        if geohash in self.geohash_cache:
            # cache hit on geohash
            return self.geohash_cache[geohash]
        # cache miss on geohash
        state = county = None
        coord = Geohash.decode(geohash)
        prop = self.get_object([float(coord[1]), float(coord[0])])
        if prop:
            state = prop['STATE']
            county = prop['COUNTY']
        self.geohash_cache[geohash] = (state, county)
        return state, county
