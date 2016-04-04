


def osm_runner(args):
    """
    Top level runner to download osm data, extract POI nodes and load into mongodb

    """
    logger.info("Starting OSM POI nodes Mongo DB loading process.")
    logger.info("outdir={0}".format(args.output))
    logger.info("states={0}".format(args.states))
    downloaded = download_osm_data(args.states)
    prepare_output_directory(args.output)
    poi_files = extract_points_of_interest(downloaded, args.output)
    load_osm_mongo(poi_files, uri=args.mongo, db=args.db, collection=args.collection)
    logger.info("Finished loading OSM POI nodes into Mongo DB")


def geojson_runner(args):
    """ Top level runner to load State and County  GeoJSON files into Mongo DB """
    logger.info("Starting States and Counties GeoJSON MongoDB DB loading process.")
    load_geo_mongo(args.file, uri=args.mongo, db=args.db, collection=args.collection)
    logger.info("Finished loading {0} into MongoDB".format(args.file))


def prepare_output_directory(outdir):
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


def download_osm_data(states):
    """
    Download data from Geofabrik

    Returns list of paths to each file that was downloaded
    """
    log = "Start data download from Geofabrik. states={0}"
    logger.info(log.format(states))
    # validate if source file containing state names exists when running in batch mode
    if not os.path.isfile(states):
        raise ValueError("state list file < {0} > does not exist".format(states))
    return Downloader().download(states)
    

def extract_points_of_interest(pbf_extracts, outdir):
    """
    Extract only OSM nodes containing specified tags

    Returns list of files containing POI nodes
    """
    log = "Extract POI nodes from downloaded pfb extracts to < {0} >"
    logger.info(log.format(outdir))
    poi_files = Extractor(tags=DEFAULT_POI_TAGS).extract(pbf_extracts, outdir)
    return poi_files


def load_osm_mongo(poi_files, uri=None, db='osm', collection=None):
    """ Read each osm file and convert each node to json and load into mongo """
    logger.info("Mongo URI: {0}".format(uri))
    logger.info("Mongo DB: {0}".format(db))
    logger.info("Mongo Collection: {0}".format(collection))
    logger.info("POI Files to be loaded < {0} >".format(poi_files))
    mongo = MongoGeo(db=db, collection=collection, uri=uri)
    OSMLoader().load(poi_files, mongo.insert)  


def load_geo_mongo(geojson, uri=None, db=None, collection=None):
    """ Load geojson file into mongodb instance """
    logger.info("Mongo URI: {0}".format(uri))
    logger.info("Mongo DB: {0}".format(db))
    logger.info("Mongo Collection: {0}".format(collection))
    logger.info("Geojson File to be loaded: {0}".format(geojson))
    mongo = MongoGeo(db=db, collection=collection, uri=uri)
    GeoJSONLoader().load(geojson, mongo.insert)  


