import os
import json

import pymongo
from pymongo import MongoClient

import logging
logger = logging.getLogger(__name__)


MONGODB_URI = os.getenv('GEOTWEET_MONGODB_URI', 'mongodb://127.0.0.1:27017')
DB = "test"
COLLECTION = "test"
PORTLAND = [-122.675983, 45.524764]
DEFAULT_TIMEOUT = 5 * 1000


class Mongo(object):
    """ Base wrapper class to connect to mongo and intialize a collection """
    
    def __init__(self, db=DB, uri=MONGODB_URI, collection=COLLECTION):
        timeout = DEFAULT_TIMEOUT
        args = dict(
            connectTimeoutMS=timeout,
            socketTimeoutMS=timeout,
            serverSelectionTimeoutMS=timeout
        )
        self.client = MongoClient(uri, **args)
        self.db = self.client[db]
        self.collection = self.db[collection]

    def insert(self, data):
        try:
            self.collection.insert_one(data)
        except pymongo.errors.DuplicateKeyError as e:
            logger.warn(str(e))
            logger.warn("Record already exists in database. Skipping")
        except pymongo.errors.WriteError as e:
            logger.warn(str(e))
            logger.warn("Write Error")


class MongoGeo(Mongo):

    def __init__(self, *args, **kwargs):
        super(MongoGeo, self).__init__(*args, **kwargs)
        self.collection.ensure_index([("geometry", "2dsphere")])

    def point(self, coordinates):
        return dict(type="Point",coordinates=coordinates)

    def find(self, query=None, limit=None):
        cmd = self.collection
        if query:
            cmd = cmd.find(query)
        else:
            cmd = cmd.find()
        if limit:
            cmd = cmd.limit(limit)
        return cmd

    def near(self, coordinates, distance=None):
        query = dict(geometry={
            "$geoNear":{
                "$geometry":self.point(coordinates),
            }
        })
        if distance:
            query['geometry']['$geoNear']['$maxDistance'] = distance
        return query

    def intersects(self, coordinates):
        return dict(geometry={
            "$geoIntersects":{
                "$geometry":self.point(coordinates)
            }
        })
