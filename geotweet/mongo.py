import os

import pymongo
from pymongo import MongoClient

from log import logger

MONGODB_URI = os.getenv('GEOTWEET_MONGODB_URI', 'mongodb://127.0.0.1:27017')
DB = "test"
COLLECTION = "test"
PORTLAND = [-122.675983, 45.524764]


class Mongo(object):
    """ Base wrapper class to connect to mongo and intialize a collection """
    
    def __init__(self, db=DB, uri=MONGODB_URI, collection=COLLECTION):
        msg = "Setting up mongo client, uri={0}, db={1}, collection={2}"
        logger.info(msg.format(uri, db, collection))
        self.client = MongoClient(uri)
        self.db = self.client[db]
        self.collection = self.db[collection]

    def insert(self, data):
        try:
            self.collection.insert_one(data)
        except pymongo.errors.DuplicateKeyError as e:
            logger.warn(str(e))
            logger.warn("Record already exists in database. Skipping")


class MongoGeo(Mongo):

    def __init__(self, *args, **kwargs):
        super(MongoGeo, self).__init__(*args, **kwargs)
        self.collection.create_index([("geometry", "2dsphere")])


class MongoQuery(Mongo):
    
    def point(self, coordinates):
        return dict(type="Point",coordinates=coordinates)

    def find(self, query=None):
        if query:
            return self.collection.find(query)
        return self.collection.find()

    def near(self, coordinates, distance):
        return dict(geometry={
            "$near":{
                "$geometry":self.point(coordinates),
                "$maxDistance": distance
            }
        })
    
    def intersects(self, coordinates):
        return dict(geometry={
            "$geoIntersects":{
                "$geometry":self.point(coordinates)
            }
        })
