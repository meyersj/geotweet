import os

import requests

from log import logger


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
        with open(tmp, 'wb') as f:
            res = requests.get(url, stream=True)
            for block in res.iter_content(1024):
                f.write(block)
        if tmp and os.path.getsize(tmp) < 500:
            error = "Small file: < {0} bytes > Failed to download: < {1} >"
            error += "\nYou may have exceeded GeoFabriks ratelimit"
            logger.error(error.format(os.path.getsize(tmp), url))
            os.remove(tmp)
            raise IOError
        return tmp
