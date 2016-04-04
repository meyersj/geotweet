import sys
import os
from os.path import dirname
import re
import json

from mrjob.job import MRJob
from mrjob.step import MRStep

root = dirname(dirname(os.path.abspath(__file__)))
sys.path.append(root)

from utils.words import WordExtractor
from mongo.mongo import MongoGeo


DB = "geotweet"
COLLECTION = "geotweet"
MIN_WORD_COUNT = 2
METERS_PER_MILE = 1609
METRO_DISTANCE = 50 * METERS_PER_MILE


class MRMetroWords(MRJob):
    """
    Map Reduce job that counts word occurences for each US Metro Area

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
                reducer_init=self.reducer_init,
                reducer=self.reducer
            )
        ]
    
    def mapper_init(self):
        self.mongo = MongoGeo(db='geotweet', collection='metro')
        self.extractor = WordExtractor()
   
    def mapper(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        expr = "|".join(["(job)", "(hiring)", "(career)"])
        if data['description'] and re.findall(expr, data['description']):
            return
        # lookup nearest metro area
        lat = data['lonlat'][1]
        lon = data['lonlat'][0]
        near = self.mongo.near([lon, lat], distance=METRO_DISTANCE)
        try:
            nearest = self.mongo.find(query=near, limit=1).next()
            metro = nearest['properties']['NAME10']
        except StopIteration:
            return
        # count each word
        for word in self.extractor.run(data['text']):
            yield (metro, word), 1
            
    def combiner(self, key, value):
        yield key, sum(value)
    
    def reducer_init(self):
        self.mongo = MongoGeo(db=DB, collection=COLLECTION)
   
    def reducer(self, key, values):
        total = int(sum(values))
        if total < MIN_WORD_COUNT:
            return
        metro, word = key
        self.mongo.insert(dict(
            metro_area=metro,
            word=word,
            count=total
        ))


if __name__ == '__main__':
    MRMetroWords.run()
