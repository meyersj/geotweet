import sys
import os
import errno
import shutil

from geotweet import Downloader
from geotweet import Extractor
from geotweet import OSMLoader
from geotweet import MongoLoader


scriptdir = os.path.dirname(os.path.realpath(__file__))

DEFAULT_OUT_DIR = os.path.join(scriptdir, 'output/poi')
DEFAULT_POI_TAGS = ['amenity', 'builing', 'shop', 'office', 'tourism']
DEFAULT_STATES = os.path.join(scriptdir, 'data/states.txt')
DEFAULT_PBF = 'http://download.geofabrik.de/north-america/us/rhode-island.osm.pbf'
DEFAULT_MONGODB_URI = 'mongodb://127.0.0.1:27017'

#AWS_KEY = os.getenv('_AWS_KEY')
#AWS_SECRET = os.getenv('_AWS_SECRET')
#AWS_REGION = 'us-west-2'

TEST_LOCAL_PBF = os.path.join(scriptdir, "data/oregon-latest.osm.pbf")


def main(args):
    """
    Usage: python runner.py [/path/to/states.txt]

    optional argument containing path to txt file containing list of US state
    names to process data for
    """
    if len(args) == 2:
        # download states listed in file passed as parameter
        runner(source=sys.argv[1], batch=True)
    else:
        runner(source=DEFAULT_STATES, batch=True)


def runner(source=DEFAULT_PBF, outdir=DEFAULT_OUT_DIR, batch=False):
    """
    Top level runner to download osm data, extract POI nodes and load into mongodb

    """
    #downloaded = download_osm_data(source, batch=batch)
    prepare_output_directory(outdir)
    downloaded = [TEST_LOCAL_PBF]
    poi_files = extract_points_of_interest(downloaded, outdir)
    load_mongo(poi_files)


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


def load_mongo(poi_files, mongo_uri=DEFAULT_MONGODB_URI):
    """
    Read each osm file and convert each node to json and load into mongo

    @param poi_files list: List of OSM files containing POI nodes
    @param mongo_uri string: [Mongo uri default='mongodb://127.0.0.1:27017']

    """
    mongo = MongoLoader('osm', uri=mongo_uri)
    OSMLoader().load(poi_files, mongo.insert)  


if __name__ == '__main__':
    main(sys.argv)
