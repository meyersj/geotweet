import sys
import os
from os.path import dirname
import re
import logging
import resource

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import RawValueProtocol, RawProtocol, JSONProtocol
import Geohash
import ujson

try:
    # when running on EMR a geotweet package will be loaded onto PYTHON PATH
    from geotweet.mapreduce.utils.lookup import CachedMetroLookup, CachedLookup
    from geotweet.mapreduce.utils.proj import project, rproject
    from geotweet.geomongo.mongo import MongoGeo
    COLLECTION = "metro_osm_emr"
except ImportError:
    # running locally
    from utils.lookup import CachedMetroLookup, CachedLookup
    from utils.proj import project, rproject
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent) 
    from geomongo.mongo import MongoGeo
    COLLECTION = "metro_osm"


DB = "geotweet"
MIN_WORD_COUNT = 2
METERS_PER_MILE = 1609
METRO_DISTANCE = 50 * METERS_PER_MILE
POI_DISTANCE = 100
MONGO_TIMEOUT = 30 * 1000
POI_TAGS = ["amenity", "builing", "shop", "office", "tourism"]
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


def dumps(src):
    return ujson.dumps(src, ensure_ascii=False)


def loads(src):
    return ujson.loads(src)


class MRMetroNearbyOSMTagCount(MRJob):
    """ """
    
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = RawProtocol
    OUTPUT_PROTOCOL = RawProtocol
    SORT_VALUES = True
    
    def steps(self):
        return [
            # lookup metro area for each geotweet and osm POI
            # and emit to same reducer to perform POI lookup
            MRStep(
                mapper_init=self.mapper_init_metro,
                mapper=self.mapper_metro,
                reducer=self.reducer_metro
            ),
            # lookup nearby POIs around geotweet
            # emit each OSM tag value that we are interested in 
            MRStep(
                reducer=self.reducer_tag_count
            ),
            # count POI tags for each metro area 
            MRStep(
                reducer_init=self.reducer_init_mongo,
                reducer=self.reducer_mongo
            )
        ]
    
    def mapper_init_metro(self):
        """ build local spatial index of US metro areas """
        self.lookup = CachedMetroLookup(precision=GEOHASH_PRECISION)
        self.hr = 0

    def mapper_metro(self, _, line):
        data = loads(line)
        if 'tags' in data:
            tag = 1
            # initalize data for POI
            lonlat = data['coordinates']
            payload = (tag, lonlat, data['tags'])
        elif 'user_id' in data:
            tag = 2
            # ignore HR geo-tweets for job postings
            expr = "|".join(["(job)", "(hiring)", "(career)"])
            if data['description'] and re.findall(expr, data['description']):
                self.hr += 1
                return
            # initialize data for getweet
            lonlat = data['lonlat']
            payload = (tag, lonlat, None)
        metro = self.lookup.get(lonlat, METRO_DISTANCE)
        if not metro:
            return
        yield metro.encode('utf-8'), dumps(payload)

    def reducer_metro(self, metro, values):
        """
        Output tags of POI locations nearby tweet locations

        Values will be sorted coming into reducer.
        First element in each value tuple will be either 1 (osm POI) or 2 (geotweet).
        Build a spatial index with POI records.
        For each tweet lookup nearby POI, and emit tag values for predefined tags.
        
        """
        lookup = CachedLookup(precision=GEOHASH_PRECISION+1)
        for i, value in enumerate(values):
            if not value:
                continue
            value = loads(value)
            mr_tag, lonlat, data = value
            if mr_tag == 1:
                # OSM POI node, add to index
                lookup.insert(i, dict(
                    geometry=dict(type='Point', coordinates=project(lonlat)),
                    properties=dict(tags=data)
                ))
            else:
                # geotweet, lookup nearest POI from index
                if not lookup.data_store:
                    return
                names = []
                kwargs = dict(buffer_size=POI_DISTANCE, multiple=True)
                # lookup nearby POI from Rtree index (caching results)
                # for any tags we care about emit the tags value and 1
                for poi in lookup.get(lonlat, **kwargs):
                    if any(tag in poi['tags'] for tag in POI_TAGS):
                        if 'name' in poi['tags']:
                            names.append(poi['tags']['name'])  
                for osm_tag in set(names):
                    if not osm_tag:
                        continue
                    key = (metro, osm_tag.encode('utf-8'))
                    yield dumps(key), dumps(1)

    def reducer_tag_count(self, key, values):
        total = 0
        if not key:
            return
        for value in values:
            if not value:
                continue
            try:
                value = loads(value)
                total += int(value)
            except ValueError as e:
                continue
        if total == 0:
            return
        metro, tag = ujson.loads(key)
        yield metro.encode('utf-8'), dumps((total, tag))

    def reducer_init_mongo(self):
        self.mongo = MongoGeo(db=DB, collection=COLLECTION, timeout=MONGO_TIMEOUT)
    
    def reducer_mongo(self, metro, values):
        if not metro:
            return
        records = []
        for record in values:
            if not record:
                continue
            try:
                total, tag = ujson.loads(record)
            except ValueError as e:
                continue
            records.append(dict(
                metro_area=metro,
                tag=tag,
                count=total
            ))
            yield dumps((metro, total)), tag.encode('utf-8')
        if records:
            self.mongo.insert_many(records)


if __name__ == '__main__':
    MRMetroNearbyOSMTagCount.run()
