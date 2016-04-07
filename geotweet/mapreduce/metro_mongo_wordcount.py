import sys
import os
from os.path import dirname
import re
import json
import logging

from mrjob.job import MRJob
from mrjob.step import MRStep


try:
    # when running on EMR a geotweet package will be loaded onto PYTHON PATH
    from geotweet.mapreduce.utils.words import WordExtractor
    from geotweet.mapreduce.utils.lookup import project, MetroLookup
    from geotweet.geomongo.mongo import MongoGeo

except ImportError:
    # running locally
    from utils.words import WordExtractor
    from utils.lookup import project, MetroLookup
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent) 
    from geomongo.mongo import MongoGeo


# must log to stderr when running on EMR or job will fail
logging.basicConfig(stream=sys.stderr, level=logging.INFO)


DB = "geotweet"
COLLECTION = "geotweet"
MIN_WORD_COUNT = 2
METERS_PER_MILE = 1609
METRO_DISTANCE = 50 * METERS_PER_MILE
MONGO_TIMEOUT = 20 * 1000


class MRMetroMongoWordCount(MRJob):
    """
    Map Reduce job that counts word occurences for each US Metro Area

    Requires a running MongoDB instance with us_metro_areas.geojson loaded

    # Command to load metro area. Must name the collection 'metro'
    `geoloader geojson /path/to/us_metro_areas.geojson metro`
    
    Mapper:

        1. Ignore tweets that appear to be from HR accounts about jobs and hiring
        2. Run MongoDB query to lookup nearest metro area based on coordinates
        3. Tokenize tweet in individual words
        4. For each word output the tuple: (('metro area', 'word'), 1)

    Reducer:

        1. Sum count for each ('metro area', 'word') key
        2. Insert record into MongoDB with word count for that metro area
    
    """

    def steps(self):
        return [
            MRStep(
                mapper_init=self.mapper_init,
                mapper=self.mapper,
                combiner=self.combiner,
                reducer=self.reducer
            ),
            MRStep(
                reducer_init=self.reducer_init_mongo,
                reducer=self.reducer_mongo
            )
        ]
    
    def mapper_init(self):
        """ build local spatial index of US metro areas """
        self.lookup = MetroLookup()
        self.extractor = WordExtractor()
   
    def mapper(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        expr = "|".join(["(job)", "(hiring)", "(career)"])
        if data['description'] and re.findall(expr, data['description']):
            return
        # lookup nearest metro area
        lonlat = project(data['lonlat'])
        nearest = self.lookup.get_object(lonlat, buffer_size=METRO_DISTANCE)
        if not nearest:
            return
        metro = nearest['NAME10']
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

    def reducer_init_mongo(self):
        self.mongo = MongoGeo(db=DB, collection=COLLECTION, timeout=MONGO_TIMEOUT)

    def reducer_mongo(self, metro, values):
        records = []
        for record in values:
            total, word = record
            records.append(dict(
                metro_area=metro,
                word=word,
                count=total
            ))
        self.mongo.insert_many(records)


if __name__ == '__main__':
    MRMetroMongoWordCount.run()
