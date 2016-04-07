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
from pyproj import Proj, transform
from reader import FileReader


# location of RTree (will only be built once and shared between mappers)
RTREE_LOCATION = '/tmp/geotweet-rtree-{0}'
# reference files to be downloaded from S3
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
COUNTIES_GEOJSON = os.path.join(AWS_BUCKET, "geotweet/us_counties102005.geojson")
METRO_GEOJSON = os.path.join(AWS_BUCKET, "geotweet/us_metro_areas102005.geojson")
# use local files if these environment variables are set with a filepath
if 'COUNTIES_GEOJSON_LOCAL' in os.environ:
    COUNTIES_GEOJSON = os.environ['COUNTIES_GEOJSON_LOCAL']
if 'METRO_GEOJSON_LOCAL' in os.environ:
    METRO_GEOJSON = os.environ['METRO_GEOJSON_LOCAL']

 
def project(lonlat):
    ESRI102500 = '+proj=eqdc +lat_0=39 +lon_0=-96 ' + \
        '+lat_1=33 +lat_2=45 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs'
    proj4326= Proj(init='epsg:4326')
    proj102500 = Proj(ESRI102500)
    return transform(proj4326, proj102500, *lonlat)


class SpatialLookup(FileReader):
    """ Create a indexed spatial lookup of a geojson file """
    
    idx = None

    def __init__(self, src=None):
        if src:
            if not self.is_valid_src(src):
                error = "Arg src=< {0} > is invalid."
                error += " Must be existing file or valid url that starts with 'http'"
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

    def get_object(self, point, buffer_size=0):
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

        geo = Point(tmp)
        if buffer_size:
            geo = geo.buffer(buffer_size)
        nearest = None
        for bbox_match in self.idx.intersection(geo.bounds, objects=True):
            # check actual geometry
            record = bbox_match.object
            try:
                if record['geometry'].intersects(geo):
                    dist = Point(tmp).distance(record['geometry'])
                    if not nearest or dist < nearest['dist']:
                        nearest = dict(data=record, dist=dist)
            except shapely.geos.TopologicalError as e:
                logging.error(e)
                logging.error(record['properties'])
        if not nearest:
            return None
        return nearest['data']['properties']
    
    def _build_obj(self, feature):
        feature['geometry'] = shape(feature['geometry'])
        return feature

    def _build(self, src, location):
        """ Build a RTree index to disk using bounding box of each feature """
        geojson = json.loads(self.read(src))
        def generate():
            for i, feature in enumerate(geojson['features']):
                feature = self._build_obj(feature)
                yield i, feature['geometry'].bounds, feature
        if geojson:
            # create index, flush to disk which disables access then re-enable access
            self.idx = index.Rtree(location, generate())
            self.idx.close()
            self.idx = index.Rtree(location)


class MetroLookup(SpatialLookup):

    def __init__(self, src=METRO_GEOJSON):
        super(MetroLookup, self).__init__(src=src)


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
