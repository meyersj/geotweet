import sys
import os
import re
import hashlib
import json
import urllib2
from urllib2 import HTTPError

from mrjob.job import MRJob
from mrjob.step import MRStep

import Geohash
import shapely
from shapely.geometry import shape
from shapely.geometry.point import Point
from rtree import index


"""
https://en.wikipedia.org/wiki/Geohash

geohash
precision   width   height
4           39.1km  19.5km
5           4.9km   4.9km
6           1.2km   609.4m
7           152.9m  152.4m
8           38.2m   19m
"""
GEOHASH_PRECISION = 7
MIN_WORD_COUNT = 5      # ignore low occurences
RTREE_LOCATION = '/tmp/geotweet-rtree-{0}'
# Reference files to be downloaded from S3
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
STOPWORDS_LIST_URL = os.path.join(AWS_BUCKET, "geotweet/stopwords.txt")
COUNTIES_GEOJSON_URL = os.path.join(AWS_BUCKET, "geotweet/us_counties.json")
# use local files if these environment variables are set with a filepath
try:
    COUNTIES_GEOJSON = os.environ['COUNTIES_GEOJSON_LOCAL']
except KeyError:
    COUNTIES_GEOJSON = COUNTIES_GEOJSON_URL
try:
    STOPWORDS_LIST = os.environ['STOPWORDS_LIST_LOCAL']
except KeyError:
    STOPWORDS_LIST = STOPWORDS_LIST_URL


class MRGeoWordCount(MRJob):
    """
    Count word occurences for US tweets by entire county, by State and County
    
    A geojson file of US counties is downloaded from an S3 bucket. A RTree index
    is built using the bounding box of each county, and is used for determining
    State and County for each tweet.
    
    """

    def steps(self):
        return [
            MRStep(
                mapper_init=self.mapper_init,
                mapper=self.mapper,
                combiner=self.combiner,
                reducer=self.reducer
            )
        ]

    def mapper_init(self):
        """ Download counties geojson from S3 and build spatial index and cache """
        self.counties = CachedCountyLookup()
        self.extractor = WordExtractor()
    
    def mapper(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        if data['description'] and self.hr_filter(data['description']):
            return
        # convert coordinates to geohash
        lat = data['lonlat'][1]
        lon = data['lonlat'][0]
        geohash = Geohash.encode(lat, lon, precision=GEOHASH_PRECISION)
        # spatial lookup for state and county
        state, county = self.counties.get(geohash) 
        if not state or not county:
            return
        # count words
        for word in self.extractor.run(data['text']):
            yield word, 1
            yield "{0}|{1}".format(word, state), 1
            yield "{0}|{1}|{2}".format(word, state, county), 1
    
    def hr_filter(self, text):
        """ check if description of twitter using contains job related key words """
        expr = "|".join(["(job)", "(hiring)", "(career)"])
        return re.findall(expr, text)
  
    def combiner(self, key, values):
        yield key, sum(values)
    
    def reducer(self, key, values):
        total = int(sum(values))
        if total < MIN_WORD_COUNT:
            return
        # parse key of the form ('word', 'word|state', 'word|state|county')
        parts = key.split('|')
        state = county = ''
        if len(parts) >= 2:
            state = parts[1]
        if len(parts) == 3:
            state = parts[1]
            county = parts[2]
        # output results
        yield (parts[0], state, county), total


class FileReader(object):
    """ Read file from the local file system or remote url """

    def is_url(self, src):
        return src.startswith('http')

    def is_valid_src(self, src):
        return os.path.isfile(src) or self.is_url(src)

    def read(self, src):
        """ Download GeoJSON file of US counties from url (S3 bucket) """
        geojson = None
        if not self.is_valid_src(src):
            error = "File < {0} > does not exists or does start with 'http'."
            raise ValueError(error.format(src))
        if not self.is_url(src):
            return open(src, 'r').read().decode('latin-1').encode('utf-8')
        response = urllib2.urlopen(src)
        return response.read().decode('latin-1').encode('utf-8')


class WordExtractor(FileReader):
    """
    Extract words from a tweet.

    If a provided `src` keyword param references a local file or remote resource
    containing list of stop words, the will be download and used to exclude
    extracted words
    
    """
    def __init__(self, src=STOPWORDS_LIST):
        self.sub_all = re.compile("""[#.!?,"(){}[\]|]|&amp;""")
        self.sub_ends = re.compile("""^[@\\\/~]*|[\\\/:~]*$""")
        self.stopwords = {}
        if src:
            if not self.is_valid_src(src):
                error = "Arg src=< {0} > is invalid."
                error += " Must be existing file or url that starts with 'http'"
                raise ValueError(error.format(src))
            words = self.read(src)
            for word in words.splitlines():
                    self.stopwords[word] = ""

    def clean_unicode(self, line):
        chars = [char for char in line.lower()]
        only_ascii = lambda char: char if ord(char) < 128 else ''
        return str(''.join(filter(only_ascii, chars)))

    def clean_punctuation(self, word):
        return self.sub_ends.sub('', self.sub_all.sub('', word))

    def run(self, line):
        """
        Extract words from tweet

        1. Remove non-ascii characters
        2. Split line into individual words
        3. Clean up puncuation characters
        
        """
        words = []
        for word in self.clean_unicode(line.lower()).split():
            if word.startswith('http'):
                continue
            cleaned = self.clean_punctuation(word)
            if len(cleaned) > 1 and cleaned not in self.stopwords:
                words.append(cleaned)
        return words


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
        return RTREE_LOCATION.format(self.digest(src))

    def digest(self, src):
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
        tmp = tuple(point)
        for bbox_match in self.idx.intersection(tmp, objects=True):
            # check actual geometry
            record = bbox_match.object
            if record['geometry'].intersects(Point(tmp)):
                return record['properties']
        return None
   
    def _build(self, src, location):
        """ Build a RTree index to disk using bounding box of each feature """
        geojson = json.loads(self.read(src))
        if geojson:
            self.idx = index.Rtree(location)
        for i, feature in enumerate(geojson['features']):
            feature['geometry'] = shape(feature['geometry'])
            self._index(i, feature)

    def _index(self, key, feature):
        """ index geojson feature using its boundin box """
        self.idx.insert(key, feature['geometry'].bounds, obj=feature)


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


if __name__ == '__main__':
    MRGeoWordCount.run()
