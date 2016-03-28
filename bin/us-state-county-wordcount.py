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
MIN_WORD_COUNT = 3 # ignore random strings


def geohash_location(lonlat, precision=6):
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
    lat = lonlat[1]
    lon = lonlat[0]
    return Geohash.encode(lat, lon, precision=precision)


class MRGeoWordCount(MRJob):

    def steps(self):
        return [
            MRStep(
                mapper=self.mapper_geohash
            ),
            MRStep(
                mapper_init=self.mapper_word_count_init,
                mapper=self.mapper_word_count,
                combiner=self.combiner_word_count,
                reducer=self.reducer_word_count
            )
        ]
    
    def mapper_geohash(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        if data['description'] and self.hr_filter(data['description']):
            return
        # convert coordinates to geohash
        geohash = geohash_location(data['lonlat'], precision=6)
        yield geohash, data['text']
    
    def mapper_word_count_init(self):
        params = dict(uri=MONGODB_URI, db="boundary", collection="counties")
        self.mongo = MongoQuery(**params)
        self.geo_lookup_cache = {}
        self.hit = 0
        self.miss = 0
    
    def mapper_word_count(self, geohash, text):
        # lookup state and county based on coordinates from tweet
        if geohash not in self.geo_lookup_cache:
            # cache miss on geohash
            self.miss += 1
            coord = Geohash.decode(geohash)
            lonlat = [float(coord[1]), float(coord[0])]
            state, county = self.geo_lookup(self.mongo, lonlat)
            self.geo_lookup_cache[geohash] = (state, county)
        else:
            # cache hit on geohash
            self.hit += 1
            state, county = self.geo_lookup_cache[geohash]
        
        #print self.hit, self.miss
        if not state or not county:
            return
        
        for word in re.findall('(\w+)', text):
            yield word, 1
            yield "{0}|{1}".format(word, state), 1
            yield "{0}|{1}|{2}".format(word, state, county), 1
    
    def combiner_word_count(self, key, values):
        yield key, sum(values)
    
    def reducer_word_count(self, key, values):
        total = int(sum(values))
        if total < MIN_WORD_COUNT:
            return
        
        parts = key.split('|')
        word = parts[0]
        state = ''
        county = ''
        if len(parts) == 2:
            state = parts[1]
        elif len(parts) == 3:
            state = parts[1]
            county = parts[2]
        yield (word, state, county), total

    def geo_lookup(self, m, lonlat):
        query = m.intersects(lonlat)
        ret = (None, None)
        try:
            match = m.find(query=query).next()
            if match:
                ret = match['properties']['STATE'], match['properties']['COUNTY']
        except StopIteration:
            pass
        return ret

    def hr_filter(self, text):
        """ check if description of twitter using contains job related key words """
        jobs = "(job[s]?)"
        hiring = "(hiring)"
        careers = "(career[s]?)"
        expr = "|".join([jobs, hiring, careers])
        return re.findall(expr, text)


if __name__ == '__main__':
    MRGeoWordCount.run()
