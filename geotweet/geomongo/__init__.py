import os
import shutil
import errno

from load import GeoJSONLoader
from mongo import MongoGeo

import logging
logger = logging.getLogger(__name__)


class GeoMongo(object):
    
    def __init__(self, args):
        self.source = args.file
        self.mongo = args.mongo
        self.db = args.db
        self.collection = args.collection

    def run(self):
        """ Top level runner to load State and County  GeoJSON files into Mongo DB """
        logger.info("Starting GeoJSON MongoDB loading process.")
        mongo = dict(uri=self.mongo, db=self.db, collection=self.collection)
        self.load(self.source, **mongo)
        logger.info("Finished loading {0} into MongoDB".format(self.source))

    def load(self, geojson, uri=None, db=None, collection=None):
        """ Load geojson file into mongodb instance """
        logger.info("Mongo URI: {0}".format(uri))
        logger.info("Mongo DB: {0}".format(db))
        logger.info("Mongo Collection: {0}".format(collection))
        logger.info("Geojson File to be loaded: {0}".format(geojson))
        mongo = MongoGeo(db=db, collection=collection, uri=uri)
        GeoJSONLoader().load(geojson, mongo.insert)  
