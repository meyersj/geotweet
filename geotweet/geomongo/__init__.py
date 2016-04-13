import os
import shutil
import errno
import logging
import sys

from load import GeoJSONLoader
from mongo import MongoGeo


class GeoMongo(object):
    
    def __init__(self, args):
        self.source = args.file
        self.mongo = args.mongo
        self.db = args.db
        self.collection = args.collection

    def run(self):
        """ Top level runner to load State and County  GeoJSON files into Mongo DB """
        logging.info("Starting GeoJSON MongoDB loading process.")
        mongo = dict(uri=self.mongo, db=self.db, collection=self.collection)
        self.load(self.source, **mongo)
        logging.info("Finished loading {0} into MongoDB".format(self.source))

    def load(self, geojson, uri=None, db=None, collection=None):
        """ Load geojson file into mongodb instance """
        logging.info("Mongo URI: {0}".format(uri))
        logging.info("Mongo DB: {0}".format(db))
        logging.info("Mongo Collection: {0}".format(collection))
        logging.info("Geojson File to be loaded: {0}".format(geojson))
        mongo = MongoGeo(db=db, collection=collection, uri=uri)
        GeoJSONLoader().load(geojson, mongo.insert)  
