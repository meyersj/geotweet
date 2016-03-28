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
GEOHASH_PRECISION = 6
MIN_WORD_COUNT = 3 # ignore random strings
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
COUNTIES_GEOJSON_URL = AWS_BUCKET + "/geotweet/us_counties.json"


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
        """ Download counties geojson from S3 and build spatial index """
        self.county_index = CountyIndex().build()
        self.geo_lookup_cache = {}
        self.hit = 0
        self.miss = 0

    def mapper(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        if data['description'] and self.hr_filter(data['description']):
            return
        # convert coordinates to geohash
        lat = data['lonlat'][1]
        lon = data['lonlat'][0]
        geohash = Geohash.encode(lat, lon, precision=GEOHASH_PRECISION)
        # spatial lookup state and county
        state, county = self.geo_lookup(geohash) 
        if not state or not county:
            return
        # count words
        for word in re.findall('(\w+)', data['text']):
            yield word, 1
            yield "{0}|{1}".format(word, state), 1
            yield "{0}|{1}|{2}".format(word, state, county), 1
    
    def combiner(self, key, values):
        yield key, sum(values)
    
    def reducer(self, key, values):
        total = int(sum(values))
        # ignore if count of occurences is below threshold
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
        # output
        yield (parts[0], state, county), total

    def geo_lookup(self, geohash):
        """ lookup state and county based on geohash of coordinates from tweet """
        state = county = None
        if geohash not in self.geo_lookup_cache:
            # cache miss on geohash
            self.miss += 1
            coord = Geohash.decode(geohash)
            county = self.county_index.search([float(coord[1]), float(coord[0])])
            if county:
                state = county['STATE']
                county = county['COUNTY']
            self.geo_lookup_cache[geohash] = (state, county)
        else:
            # cache hit on geohash
            self.hit += 1
            state, county = self.geo_lookup_cache[geohash]
        return (state, county)

    def hr_filter(self, text):
        """ check if description of twitter using contains job related key words """
        expr = "|".join(["(job)", "(hiring)", "(career)"])
        return re.findall(expr, text)


class CountyIndex(object):
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

    def search(self, point):
        """ lookup county based on point as [longitude, latitude] """
        # first search bounding boxes
        for i in self.idx.intersection(point):
            # check actual geometry
            if self.data[i]['geometry'].intersects(Point(point)):
                return self.data[i]['properties']
        return None


if __name__ == '__main__':
    MRGeoWordCount.run()
