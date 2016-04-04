import os
import shutil
import errno

from download import Downloader
from extract import Extractor
from load import OSMLoader, GeoJSONLoader
from ..mongo.mongo import MongoGeo

import logging
logger = logging.getLogger(__name__)


DEFAULT_POI_TAGS = ['amenity', 'builing', 'shop', 'office', 'tourism']


class Geo(object):
    
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


class OSM(object):

    def __init__(self, args):
        self.output = args.output
        self.states = args.states
        self.mongo = args.mongo
        self.db = args.db
        self.collection = args.collection

    def run(self):
        """
        Top level runner to download osm data, extract POI nodes and load into mongodb

        """
        log = "Using states list at: < {0} >"
        logger.info(log.format(self.states))
        logger.info("Starting OSM POI nodes Mongo DB loading process.")
        logger.info("outdir={0}".format(self.output))
        logger.info("states={0}".format(self.states))
        # start pipeline 
        downloaded = self.download(self.states)
        self.prep_output(self.output)
        poi_files = self.extract(downloaded, self.output)
        self.load(poi_files, uri=self.mongo, db=self.db, collection=self.collection)
        logger.info("Finished loading OSM POI nodes into Mongo DB")
    
    def download(self, states):
        """
        Download data from Geofabrik

        Returns list of paths to each file that was downloaded
        """
        log = "Start data download from Geofabrik. states={0}"
        logger.info(log.format(states))
        # validate if source file containing state names exists
        if not os.path.isfile(states):
            raise ValueError("state list file < {0} > does not exist".format(states))
        return Downloader().download(states)

    def prep_output(self, outdir):
        """ Clear output directory and create if does not exist """
        logger.info("Cleaning output directory < {0} >".format(outdir))
        try:
            shutil.rmtree(outdir, ignore_errors=True)
        except Exception as e:
            print e
        try:
            os.makedirs(outdir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(outdir):
                pass

    def extract(self, pbf_extracts, outdir):
        """
        Extract only OSM nodes containing specified tags

        Returns list of files containing POI nodes
        """
        log = "Extract POI nodes from downloaded pfb extracts to < {0} >"
        logger.info(log.format(outdir))
        poi_files = Extractor(tags=DEFAULT_POI_TAGS).extract(pbf_extracts, outdir)
        return poi_files

    def load(self, poi_files, uri=None, db='osm', collection=None):
        """ Read each osm file and convert each node to json and load into mongo """
        logger.info("Mongo URI: {0}".format(uri))
        logger.info("Mongo DB: {0}".format(db))
        logger.info("Mongo Collection: {0}".format(collection))
        logger.info("POI Files to be loaded < {0} >".format(poi_files))
        mongo = MongoGeo(db=db, collection=collection, uri=uri)
        OSMLoader().load(poi_files, mongo.insert)  
