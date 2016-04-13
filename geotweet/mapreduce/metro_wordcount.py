import sys
import os
from os.path import dirname
import re
import json
import logging

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import JSONProtocol, JSONValueProtocol, RawValueProtocol
from pymongo.errors import ServerSelectionTimeoutError

try:
    # when running on EMR a geotweet package will be loaded onto PYTHON PATH
    from geotweet.mapreduce.utils.words import WordExtractor
    from geotweet.mapreduce.utils.proj import project
    from geotweet.mapreduce.utils.lookup import CachedMetroLookup
    from geotweet.geomongo.mongo import MongoGeo
except ImportError:
    # running locally
    from utils.words import WordExtractor
    from utils.proj import project
    from utils.lookup import CachedMetroLookup
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent) 
    from geomongo.mongo import MongoGeo


# must log to stderr when running on EMR or job will fail
logging.basicConfig(stream=sys.stderr, level=logging.INFO)


DB = "geotweet"
COLLECTION = "metro_word"
MIN_WORD_COUNT = 2
METERS_PER_MILE = 1609
METRO_DISTANCE = 50 * METERS_PER_MILE
MONGO_TIMEOUT = 20 * 1000
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


class MRMetroMongoWordCount(MRJob):
    """
    Map Reduce job that counts word occurences for each US Metro Area

    Requires a running MongoDB instance with us_metro_areas.geojson loaded
    
    Mapper Init:

        1. Build local Rtree spatial index of US metro areas
            - geojson file downloaded from S3 bucket

    Mapper:

        1. Ignore tweets that appear to be from HR accounts about jobs and hiring
        2. Lookup nearest metro area from spatial index using coordinates
        3. Tokenize tweet in individual words
        4. For each word output the tuple: (('metro area', 'word'), 1)

    Reducer:

        1. Sum count for each ('metro area', 'word') key
        2. Insert record into MongoDB with word count for that metro area
    
    Reducer Mongo:

        1. Build list of all documents for each metro area and insert as batch
        into MongoDB

    """
    
    INPUT_PROTOCOL = JSONValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawValueProtocol

    def steps(self):
        return [
            MRStep(
                mapper_init=self.mapper_init,
                mapper=self.mapper,
                combiner=self.combiner,
                reducer=self.reducer
            ),
            MRStep(
                reducer_init=self.reducer_init_output,
                reducer=self.reducer_output
            )
        ]
    
    def mapper_init(self):
        """ build local spatial index of US metro areas """
        self.lookup = CachedMetroLookup(precision=GEOHASH_PRECISION)
        self.extractor = WordExtractor()
   
    def mapper(self, _, data):
        # ignore HR geo-tweets for job postings
        expr = "|".join(["(job)", "(hiring)", "(career)"])
        if data['description'] and re.findall(expr, data['description']):
            return
        # lookup nearest metro area
        metro = self.lookup.get(data['lonlat'], METRO_DISTANCE)
        if not metro:
            return
        # count each word
        for word in self.extractor.run(data['text']):
            yield (metro, word), 1
            
    def combiner(self, key, value):
        yield key, sum(value)
   
    def reducer(self, key, values):
        total = int(sum(values))
        if total < MIN_WORD_COUNT:
            return
        metro, word = key
        yield metro, (total, word)

    def reducer_init_output(self):
        """ establish connection to MongoDB """
        try:
            self.mongo = MongoGeo(db=DB, collection=COLLECTION, timeout=MONGO_TIMEOUT)
        except ServerSelectionTimeoutError:
            # failed to connect to running MongoDB instance
            self.mongo = None
    
    def reducer_output(self, metro, values):
        records = []
        for record in values:
            total, word = record
            records.append(dict(
                metro_area=metro,
                word=word,
                count=total
            ))
            output = "{0}\t{1}\t{2}"
            output = output.format(metro.encode('utf-8'), total, word.encode('utf-8'))
            yield None, output
        if self.mongo:
            self.mongo.insert_many(records)


if __name__ == '__main__':
    MRMetroMongoWordCount.run()
