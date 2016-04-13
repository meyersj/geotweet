import sys
import os
import re

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import JSONProtocol, JSONValueProtocol, RawValueProtocol

try:
    # when running on EMR the geotweet package will be installed with pip
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
METRO_GEOHASH_PRECISION = 7
POI_GEOHASH_PRECISION = 8
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


class POINearTweetsMRJob(MRJob):
    """ Count common OSM points-of-interest around Tweets with coordinates """
    
    INPUT_PROTOCOL = JSONValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawValueProtocol
    SORT_VALUES = True
    
    def steps(self):
        return [
            # 1. lookup metro area for each geotweet and osm POI
            #     emit to same reducer to perform POI lookup
            # 2. lookup nearby osm POIs around each geotweet
            # 3. emit metro area + name of POI and 1 to count
            MRStep(
                mapper_init=self.mapper_init_metro,
                mapper=self.mapper_metro,
                reducer=self.reducer_metro
            ),
            # aggregate count for each (metro area, POI) 
            MRStep(
                reducer=self.reducer_count
            ),
            # convert output to final form and persist to Mongo
            MRStep(
                reducer_init=self.reducer_init_output,
                reducer=self.reducer_output
            )
        ]
    
    def mapper_init_metro(self):
        """ build local spatial index of US metro areas """
        self.lookup = CachedMetroLookup(precision=METRO_GEOHASH_PRECISION)

    def mapper_metro(self, _, data):
        """ map each osm POI and geotweets based on spatial lookup of metro area """
        # OSM POI record
        if 'tags' in data:
            type_tag = 1
            lonlat = data['coordinates']
            payload = data['tags']
        # Tweet with coordinates from Streaming API
        elif 'user_id' in data:
            type_tag = 2
            # only allow tweets from the above known domains to try and filter out
            # noise such as HR tweets, Weather reports and news updates
            accept = [
                "twitter\.com",
                "foursquare\.com",
                "instagram\.com",
                "untappd\.com"
            ]
            expr = "|".join(accept)
            if not re.findall(expr, data['source']):
                return
            lonlat = data['lonlat']
            payload = None
        # spatial lookup using Rtree and caching results
        metro = self.lookup.get(lonlat, METRO_DISTANCE)
        if not metro:
            return
        yield metro, (type_tag, lonlat, payload)

    def reducer_metro(self, metro, values):
        """
        Output tags of POI locations nearby tweet locations

        Values will be sorted coming into reducer.
        First element in each value tuple will be either 1 (osm POI) or 2 (geotweet).
        Build a spatial index with POI records.
        For each tweet lookup nearby POI, and emit tag values for predefined tags.
        
        """
        lookup = CachedLookup(precision=POI_GEOHASH_PRECISION)
        for i, value in enumerate(values):
            type_tag, lonlat, data = value
            if type_tag == 1:
                # OSM POI node, add to index
                lookup.insert(i, dict(
                    geometry=dict(type='Point', coordinates=project(lonlat)),
                    properties=dict(tags=data)
                ))
            else:
                # geotweet, lookup nearest POI from index
                if not lookup.data_store:
                    return
                poi_names = []
                kwargs = dict(buffer_size=POI_DISTANCE, multiple=True)
                # lookup nearby POI from Rtree index (caching results)
                # for any tags we care about emit the tags value and 1
                for poi in lookup.get(lonlat, **kwargs):
                    has_tag = [ tag in poi['tags'] for tag in POI_TAGS ]
                    if any(has_tag) and 'name' in poi['tags']:
                        poi_names.append(poi['tags']['name'])
                for poi in set(poi_names):
                    yield (metro, poi), 1

    def reducer_count(self, key, values):
        """ count occurences for each (metro, POI) record """
        total = sum(values)
        metro, poi = key
        # group data by metro areas for final output    
        yield metro, (total, poi)

    def reducer_init_output(self):
        """ establish connection to MongoDB """
        self.mongo = MongoGeo(db=DB, collection=COLLECTION, timeout=MONGO_TIMEOUT)
    
    def reducer_output(self, metro, values):
        """ store each record in MongoDB and output tab delimited lines """
        records = []
        # build up list of data for each metro area and submit as one network
        # call instead of individually 
        for value in values:
            total, poi = value
            records.append(dict(
                metro_area=metro,
                poi=poi,
                count=total
            ))
            output = "{0}\t{1}\t{2}"
            output = output.format(metro.encode('utf-8'), total, poi.encode('utf-8'))
            yield None, output
        self.mongo.insert_many(records)


if __name__ == '__main__':
    POINearTweetsMRJob.run()
