import json
import sys
import os
import errno
import shutil

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.download import Downloader
from geotweet.extract import Extractor
from geotweet.load import OSMLoader, GeoJSONLoader
from geotweet.mongo import MongoGeo
from geotweet.log import logger


parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

TEST_LOCAL_PBF = os.path.join(DATA_DIR, "rhode-island-latest.osm.pbf")
DEFAULT_PBF = 'http://download.geofabrik.de/north-america/us/rhode-island.osm.pbf'
MONGODB_URI = os.getenv('GEOTWEET_MONGODB_URI', 'mongodb://127.0.0.1:27017')

DEFAULT_POI_TAGS = ['amenity', 'builing', 'shop', 'office', 'tourism']
DATA_DIR = os.path.join(parentdir, 'data')
DEFAULT_OUT_DIR = os.path.join(parentdir, 'output/poi')
DEFAULT_STATES = os.path.join(DATA_DIR, 'states.txt')


def main(args):
    """
    Usage: python loader.py [osm|boundary] [/path/to/states.txt]

    optional argument containing path to txt file containing list of US state
    names to process data for
    """
    
    usage = "Usage: python loader.py [osm|boundary] [/path/to/states.txt]"

    if len(args) >= 2:
        cmd = args[1]
        if cmd == "osm":
            if len(args) >= 3:
                # download states listed in file passed as parameter
                osm_runner(source=sys.argv[2], batch=True)
            else:
                osm_runner(source=DEFAULT_STATES, batch=True)
        elif cmd == "boundary":
            boundary_runner()
        else:
            print usage


def osm_runner(source=DEFAULT_PBF, outdir=DEFAULT_OUT_DIR, batch=False):
    """
    Top level runner to download osm data, extract POI nodes and load into mongodb

    """
    logger.info("Starting osm runner")
    logger.info("batch={0}".format(batch))
    logger.info("outdir={0}".format(source))
    logger.info("source={0}".format(source))
    
    logger.info("Start data download from Geofabrik")
    downloaded = download_osm_data(source, batch=batch)
    logger.info("Finished downloading data")

    logger.info("Cleaning output directory {0}".format(outdir))
    prepare_output_directory(outdir)
    
    downloaded = [TEST_LOCAL_PBF]
    
    poi_files = extract_points_of_interest(downloaded, outdir)
    logger.info("poi files that were extracted: {0}".format(poi_files))
    
    logger.info("Loading POI Files into mongo: {0}".format(MONGODB_URI))
    load_osm_mongo(poi_files)
    logger.info("Finished Loading POI Files")


def boundary_runner():
    data = os.path.join(DATA_DIR, 'us_states.json')
    logger.info("Loading GeoJSON into mongodb: {0}".format(data))
    load_geo_mongo('states', data)

    data = os.path.join(DATA_DIR, 'us_counties.json')
    logger.info("Loading GeoJSON into mongodb: {0}".format(data)) 
    load_geo_mongo('counties', data)

    logger.info("Finished loading state and county boundary files")


def prepare_output_directory(outdir):
    """
    Clear output directory and create if does not exist 
    
    """
    try:
        shutil.rmtree(outdir, ignore_errors=True)
    except Exception as e:
        print e
    try:
        os.makedirs(outdir)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(outdir):
            pass


def download_osm_data(source, batch=False):
    """
    Download data from Geofabrik

    @param source string: Path to file containing list of state names or url to
                          Geofabrik pfb extract
    @param batch bool: Flag to download a single file or download multiple files
                       listed in source file
    
    @return Return list of paths to each file that was downloaded
    
    """
    # validate if source file containing state names exists when running in batch mode
    if batch and not os.path.isfile(source):
        raise ValueError("state list file < {0} > does not exist".format(source))

    dl = Downloader()
    if batch:
        # download states listed in source file
        return dl.download(source)
    # download single file using url specified by source
    return [dl._download(source)]
    

def extract_points_of_interest(pbf_extracts, outdir):
    """
    Extract only OSM nodes containing specified tags

    @param pbf_extracts list: List of OSM pbf files downloaded from Geofabrik
    @param outdir string: Path to output directory to contain OSM files of POI nodes
    
    @return Returns list of files containing POI nodes
    
    """
    poi_files = Extractor(tags=DEFAULT_POI_TAGS).extract(pbf_extracts, outdir)
    return poi_files


def load_osm_mongo(poi_files, mongo_uri=MONGODB_URI):
    """
    Read each osm file and convert each node to json and load into mongo

    @param poi_files list: List of OSM files containing POI nodes
    @param mongo_uri string: [Mongo uri default='mongodb://127.0.0.1:27017']

    """
    mongo = MongoGeo(db='osm', collection='poi', uri=mongo_uri)
    OSMLoader().load(poi_files, mongo.insert)  


def load_geo_mongo(collection, json_file, uri=MONGODB_URI):
    """
    Load geojson file into mongodb instance
    
    @param collection string: Name of mongodb collection
    @param json_file string: Path to json file

    """
    mongo = MongoGeo(db='boundary', collection=collection, uri=uri)
    GeoJSONLoader().load(json_file, mongo.insert)  


if __name__ == '__main__':
    main(sys.argv)
