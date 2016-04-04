import sys
import os
from os.path import dirname
import re
import json

from mrjob.job import MRJob
from mrjob.step import MRStep

import Geohash

#root = dirname(dirname(os.path.abspath(__file__)))
#sys.path.append(root)

from utils.reader import FileReader
from utils.words import WordExtractor
from utils.lookup import CachedCountyLookup


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


if __name__ == '__main__':
    MRGeoWordCount.run()
