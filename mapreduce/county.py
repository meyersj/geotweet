import sys
import os
from os.path import dirname
import re
import json

from mrjob.job import MRJob
from mrjob.step import MRStep

import Geohash

root = dirname(dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet_utils.reader import FileReader
from geotweet_utils.words import WordExtractor
from geotweet_utils.mongo import MongoGeo


"""
https://en.wikipedia.org/wiki/Geohash

geohash
precision   width   height
4           39.1km  19.5km
5           4.9km   4.9km
6           1.2km   609.4m
"""
GEOHASH_PRECISIONS = [4, 5, 6]
MIN_WORD_COUNT = 2
DB = "geotweet"
COLLECTION = "geotweet"



class MRCountyWords(MRJob):

    def steps(self):
        return [
            MRStep(
                mapper=self.user_mapper,
                combiner=self.user_combiner,
                reducer=self.user_reducer
            ),
            MRStep(
                mapper_init=self.word_mapper_init,
                mapper=self.word_mapper,
                combiner=self.word_combiner,
                reducer_init=self.word_reducer_init,
                reducer=self.word_reducer
            )
        ]
   
    def user_mapper(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        if data['description'] and self.hr_filter(data['description']):
            return
        if not data['description']:
            return
        yield data['user_id'], (data['description'], data['lonlat'])
    
    def hr_filter(self, text):
        """ check if description of twitter using contains job related key words """
        expr = "|".join(["(job)", "(hiring)", "(career)"])
        return re.findall(expr, text)
   
    def user_combiner(self, key, values):
        yield key, values.next()
     
    def user_reducer(self, key, values):
        yield None, values.next()
    
    def word_mapper_init(self):
        """ Download counties geojson from S3 and build spatial index and cache """
        self.extractor = WordExtractor()

    def word_mapper(self, key, line):
        # ignore HR geo-tweets for job postings
        # convert coordinates to geohash
        lat = line[1][1]
        lon = line[1][0]
        geohashes = []
        for precision in GEOHASH_PRECISIONS:
            geohashes.append(Geohash.encode(lat, lon, precision=precision))
        for word in self.extractor.run(line[0]):
            for geohash in geohashes:
                yield "{0}|{1}".format(geohash, word), 1
  
    def word_combiner(self, key, values):
        yield key, sum(values)
    
    def word_reducer_init(self):
        self.mongo = MongoGeo(db=DB, collection=COLLECTION)
   
    def word_reducer(self, key, values):
        total = int(sum(values))
        if total < MIN_WORD_COUNT:
            return
        # parse key of the form 'geohash|word'
        geohash, word = key.split('|')
        coord = Geohash.decode(geohash)
        geometry = dict(type='Point', coordinates=[float(coord[1]), float(coord[0])])
        content = dict(
            geometry=geometry,
            word=word,
            precision=len(geohash),
            total=total,
            geohash=geohash
        )
        self.mongo.insert(content)


if __name__ == '__main__':
    MRCountyWords.run()
