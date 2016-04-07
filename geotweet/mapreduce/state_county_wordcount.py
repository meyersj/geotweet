import sys
import os
from os.path import dirname
import re
import json
import logging

from mrjob.job import MRJob
from mrjob.step import MRStep

import Geohash


try:
    # when running on EMR a geotweet package will installed with pip
    from geotweet.mapreduce.utils.words import WordExtractor
    from geotweet.mapreduce.utils.lookup import project, CachedCountyLookup
except ImportError:
    # when running locally utils using relative import
    from utils.words import WordExtractor
    from utils.lookup import project, CachedCountyLookup


# must log to stderr when running on EMR or job will fail
logging.basicConfig(stream=sys.stderr, level=logging.INFO)


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
MIN_WORD_COUNT = 5              # ignore low occurences


class MRStateCountyWordCount(MRJob):
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
        # project coordinates to ESRI:102005 and encode as geohash
        lon, lat = project(data['lonlat'])
        geohash = Geohash.encode(lat, lon, precision=GEOHASH_PRECISION)
        # spatial lookup for state and county
        state, county = self.counties.get(geohash) 
        if not state or not county:
            return
        # count words
        for word in self.extractor.run(data['text']):
            yield (word, ), 1
            yield (word, state), 1
            yield (word, state, county), 1
    
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
        word = state = county = None
        word = key[0]
        if len(key) >= 2:
            state = key[1]
        if len(key) >= 3:
            county = key[2]
        yield (word, state, county), total


if __name__ == '__main__':
    MRStateCountyWordCount.run()
