import sys
import os
import re
import json
import heapq

from mrjob.job import MRJob
from mrjob.step import MRStep

import Geohash

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.mongo import MongoQuery


MONGODB_URI = os.getenv('GEOTWEET_MONGODB_URI', 'mongodb://127.0.0.1:27017')


class MRGeoWordCount(MRJob):

    def steps(self):
        return [
            MRStep(
                mapper_init=self.mapper_init,
                mapper=self.mapper_count,
                mapper_final=self.mapper_final,
                combiner=self.combiner_count,
                reducer=self.reducer_count
            ),
            MRStep(
                reducer=self.reducer_top
            )
        ]

    def mapper_init(self):
        kwargs = dict(uri=MONGODB_URI, db="boundary")
        kwargs['collection'] ='states'
        self.mongo_states = MongoQuery(**kwargs)
        kwargs['collection'] = 'counties'
        self.mongo_counties = MongoQuery(**kwargs)
        self.geo_lookup_cache = {}
        self.hit = 0
        self.miss = 0

    def mapper_count(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        if data['description'] and self.hr_filter(data['description']):
            return
        
        geohash = self.geohash(data, precision=6)
        if geohash not in self.geo_lookup_cache:
            self.miss += 1
            # lookup the county and state the tweet was from
            # run word count for all words and for words in each state and county
            #print data['text'], data['lonlat']
            state = self.geo_lookup(self.mongo_states, data['lonlat'])
            county = self.geo_lookup(self.mongo_counties, data['lonlat'])
            self.geo_lookup_cache[geohash] = (state, county)
        else:
            self.hit += 1
            state, county = self.geo_lookup_cache[geohash]
        
        self.map_words(data['text'], state, county)
    
    def mapper_final(self):
        print
        print "HIT {0}".format(self.hit)
        print "MISS {0}".format(self.miss)
        print
  
    def map_words(self, text, state, county):
        for word in re.findall('(\w+)', text):
            yield word, 1
            if state: 
                yield "{0}-{1}".format(word, state, word), 1
                if county:
                    yield "{0}-{1}-{2}".format(word, state, county), 1

    def combiner_count(self, key, values):
        yield key, sum(values)
    
    def reducer_count(self, key, values):
        yield None, (sum(values), key)
        
    def reducer_top(self, _, values):
        heap = []
        for value in values:
            heapq.heappush(heap, value)

        for value in heapq.nlargest(100, heap):
            key = value[0].split('-')
            word = key[0]
            count = value[1]
            yield word, count
    
    def geo_lookup(self, m, lonlat):
        query = m.intersects(lonlat)
        try:
            match = m.find(query=query).next()
            if match:
                return match['properties']['NAME']
        except StopIteration:
            return None
        return None

    def hr_filter(self, text):
        """ check if description of twitter using contains job related key words """
        jobs = "(job[s]?)"
        hiring = "(hiring)"
        careers = "(career[s]?)"
        expr = "|".join([jobs, hiring, careers])
        return re.findall(expr, text)

    def geohash(self, data, precision=6):
        """
        Compute geohash from coordinates
    
        https://en.wikipedia.org/wiki/Geohash
    
        geohash
        length  width   height
        4       39.1km  19.5km
        5       4.9km   4.9km
        6       1.2km   609.4m
        7       152.9m  152.4m
        8       38.2m   19m
        
        """
        lat = data['lonlat'][1]
        lon = data['lonlat'][0]
        return Geohash.encode(lon, lat, precision=precision)


if __name__ == '__main__':
    MRGeoWordCount.run()
