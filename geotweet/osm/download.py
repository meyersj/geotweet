import os
import re

import requests

import logging
logger = logging.getLogger(__name__)


US_GEOFABRIK = 'http://download.geofabrik.de/north-america/us/{0}-latest.osm.pbf'


class Downloader(object):
    """
    Downloads OSM extracts from GeoFabrik in pbf format

    """
    
    def build_url(self, state):
        return US_GEOFABRIK.format(state.replace(' ', '-').lower())

    def get_filename(self, url):
        filename = url.rsplit('/', 1)[-1]
        return os.path.join('/tmp', filename)
    
    def download(self, states_file):
        """ For each state in states file build url and download file """
        outfiles = []
        with open(states_file, 'r') as f:
            for state in f.read().splitlines():
                url = self.build_url(state)
                log = "Downloading State < {0} > from < {1} >"
                logger.info(log.format(state, url))
                outfiles.append(self._download(url))
        return outfiles

    def _download(self, url):
        """ Dowload file to /tmp """
        tmp = self.get_filename(url)
        f = open(tmp, 'wb')
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
