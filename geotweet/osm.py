import os
import sys
import json
from os.path import dirname

import requests
from imposm.parser import OSMParser


from .twitter.load import S3Loader

import logging
logger = logging.getLogger(__name__)


SCRIPTDIR = dirname(os.path.abspath(__file__))
DEFAULT_STATES = os.path.join(SCRIPTDIR, 'data/states.txt')
US_GEOFABRIK = 'http://download.geofabrik.de/north-america/us/{0}-latest.osm.pbf'
POI_TAGS = ["amenity", "builing", "shop", "office", "tourism"]


class OSMRunner(object):
    """
    Downloads OSM extracts from GeoFabrik in pbf format

    """
    def __init__(self, args):
        self.states = args.states
        if not args.states:
            self.states = DEFAULT_STATES
        self.output = args.output
        self.overwrite = False
        self.s3 = S3Loader(bucket=args.bucket, region=args.region)
        try:
            self.s3.valid()
        except EnvironmentError as e:
            logger.error(e)
            sys.exit(1)
      


    def run(self):
        """ For each state in states file build url and download file """
        states = open(self.states, 'r').read().splitlines()
        for state in states:
            url = self.build_url(state)
            log = "Downloading State < {0} > from < {1} >"
            logging.info(log.format(state, url))
            tmp = self.download(self.output, url, self.overwrite)
            self.s3.store(self.extract(tmp, self.tmp2poi(tmp)))
    
    def download(self, output_dir, url, overwrite):
        """ Dowload file to /tmp """
        tmp = self.url2tmp(output_dir, url)
        if os.path.isfile(tmp) and not overwrite:
            logger.info("File {0} already exists. Skipping download.".format(tmp))
            return tmp
        f = open(tmp, 'wb')
        logger.info("Downloading {0}".format(url))
        res = requests.get(url, stream=True)
        if res.status_code != 200:
            # failed to download, cleanup and raise exception
            f.close()
            os.remove(tmp)
            error = "{0}\n\nFailed to download < {0} >".format(res.content, url)
            raise IOError(error)
        for block in res.iter_content(1024):
            f.write(block)
        f.close()
        return tmp

    def extract(self, pbf, output):
        """ extract POI nodes from osm pbf extract """
        logger.info("Extracting POI nodes from {0} to {1}".format(pbf, output))
        with open(output, 'w') as f:
            # define callback for each node that is processed
            def nodes_callback(nodes):
                for node in nodes:
                    node_id, tags, coordinates = node
                    # if any tags have a matching key then write record
                    if any([t in tags for t in POI_TAGS]):
                        f.write(json.dumps(dict(tags=tags, coordinates=coordinates)))
                        f.write('\n')
            parser = OSMParser(concurrency=4, nodes_callback=nodes_callback)
            parser.parse(pbf)
        return output
    
    def build_url(self, state):
        return US_GEOFABRIK.format(state.replace(' ', '-').lower())

    def url2tmp(self, root, url):
        """ convert url path to filename """
        filename = url.rsplit('/', 1)[-1]
        return os.path.join(root, filename)

    def tmp2poi(self, osm):
        return osm.rsplit('.', 2)[0] + '.poi'
