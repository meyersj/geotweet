import sys
import os
import re
import json
import urllib2

from mrjob.job import MRJob
from mrjob.step import MRStep

import Geohash
import shapely
from shapely.geometry import shape
from shapely.geometry.point import Point
from rtree import index


GEOHASH_PRECISION = 7
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

MIN_WORD_COUNT = 5      # ignore low occurences

# Reference files to be downloaded from S3
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
COUNTIES_GEOJSON_URL = os.path.join(AWS_BUCKET, "geotweet/us_counties.json")
STOPWORDS_URL = os.path.join(AWS_BUCKET, "geotweet/stopwords.txt")


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
        self.counties = CountyLookup()
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


class WordExtractor(object):
    
    def __init__(self, stopwords=STOPWORDS_URL):
        self.sub_all = re.compile("""[#.!?,"(){}[\]|]|&amp;""")
        self.sub_ends = re.compile("""^[@\\\/~]*|[\\\/:~]*$""")
        self.stopwords = {}
        if stopwords:
            words = self.download(stopwords)
            for word in words.splitlines():
                    self.stopwords[word] = ""
    
    def download(self, url):
        """ Download stopwords.txt file from url (S3 bucket) """
        response = urllib2.urlopen(url)
        return response.read()

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


class CountyLookup(object):
    """ Dowload counties geojson, build index and provide lookup functionality """
    
    def __init__(self):
        self.index = CountySpatialIndex().build()
        self.geohash_cache = {}
   
    def get(self, geohash):
        """ lookup state and county based on geohash of coordinates from tweet """
        if geohash in self.geohash_cache:
            # cache hit on geohash
            return self.geohash_cache[geohash]
        # cache miss on geohash
        state = county = None
        coord = Geohash.decode(geohash)
        prop = self.index.get([float(coord[1]), float(coord[0])])
        if prop:
            state = prop['STATE']
            county = prop['COUNTY']
        self.geohash_cache[geohash] = (state, county)
        return state, county


class CountySpatialIndex(object):
    """ Create an local spatial index of all counties in the US """
 
    def build(self, url=COUNTIES_GEOJSON_URL):
        """ Build a RTree index using bounding box of each US county """
        self.idx = index.Index()
        self.data = {}
        counties = json.loads(self.download(url))
        for i, feature in enumerate(counties['features']):
            feature['geometry'] = shape(feature['geometry'])
            self.index(i, feature)
        return self

    def download(self, url):
        """ Download GeoJSON file of US counties from url (S3 bucket) """
        response = urllib2.urlopen(url)
        try:
            return response.read().decode('latin-1').encode('utf-8')
        except Exception as e:
            print e
            sys.exit(1)

    def index(self, key, feature):
        """
        add geojson feature to bounding box index
        
        feature is geojson dict where 'geometry' key is a shapely.geometry object
        """
        self.idx.insert(key, feature['geometry'].bounds)
        self.data[key] = feature

    def get(self, point):
        """ lookup county based on point as [longitude, latitude] """
        # first search bounding boxes
        for i in self.idx.intersection(point):
            # check actual geometry
            if self.data[i]['geometry'].intersects(Point(point)):
                return self.data[i]['properties']
        return None


if __name__ == '__main__':
    MRGeoWordCount.run()
