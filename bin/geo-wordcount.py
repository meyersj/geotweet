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


def print_location(data, match):
    print "Location Tag"
    print "@", match[1]
    print match[0]
    print "source", data["source"]
    print "link", match[2]
    print data["text"]
    print


def print_unknown(data):
    print "Unknown"
    print data['screen_name']
    print "desc", data['description']
    print data['text']
    print "source", data["source"]
    print


class MRGeoWordCount(MRJob):

    def steps(self):
        return [
            MRStep(
                mapper=self.mapper_count,
                combiner=self.combiner_count,
                reducer=self.reducer_count
            ),
            MRStep(
                reducer=self.reducer_top
            )
        ]
   
    def mapper_count(self, _, line):
        data = json.loads(line)
        # ignore HR geo-tweets for job postings
        if data['description'] and self.hr_filter(data['description']):
            return

        # lookup the county and state the tweet was from
        # run word count for all words and for words in each state and county
        state = self.geo_lookup("states", data['lonlat'])
        county = self.geo_lookup("counties", data['lonlat'])
        for word in re.findall('(\w+)', data['text']):
            yield word, 1
            if state: 
                yield "{0}-{1}".format(state, word), 1
                if county:
                    yield "{0}-{1}-{2}".format(state, county, word), 1
    
    def combiner_count(self, key, values):
        yield key, sum(values)
    
    def reducer_count(self, key, values):
        yield None, (sum(values), key)
        
    def reducer_top(self, _, values):
        heap = []
        for value in values:
            heapq.heappush(heap, value)

        for x in heapq.nlargest(100, heap):
            yield x[0], x[1]
    
    def geo_lookup(self, collection, lonlat):
        m = MongoQuery(uri=MONGODB_URI, db="boundary", collection=collection)
        query = m.intersects(lonlat)
        match = m.find(query=query).next()
        if match:
            return match['properties']['NAME']
        return None

    def hr_filter(self, text):
        """ check if description of twitter using contains job related key words """
        jobs = "(job[s]?)"
        hiring = "(hiring)"
        careers = "(career[s]?)"
        expr = "|".join([jobs, hiring, careers])
        return re.findall(expr, text)

    #def geohash(self, data, precision=5):
    #    """
    #    Compute geohash from coordinates
    #
    #    https://en.wikipedia.org/wiki/Geohash
    #
    #    geohash
    #    length  width   height
    #    4       39.1km  19.5km
    #    5       4.9km   4.9km
    #    6       1.2km   609.4m
    #    7       152.9m  152.4m
    #    8       38.2m   19m
    #    9       4.8m    4.8m
    #    
    #    """
    #    lat = data['lonlat'][1]
    #    lon = data['lonlat'][0]
    #    return Geohash.encode(lon, lat, precision=precision)
    
    #def geotag_filter(self, text):
    #    """
    #    Match geo-tagged tweets of the form:
    #        Tweet ... @ Location Name https://instaface.com/something
    #    
    #    """
    #    location = re.findall('(.*) @ (.*)( http.*)?', text)
    #    if location and len(location) == 1:
    #        return location[0]
    #    return False


if __name__ == '__main__':
    MRGeoWordCount.run()
