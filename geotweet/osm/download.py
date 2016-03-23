import os

import requests


US_GEOFABRIK = 'http://download.geofabrik.de/north-america/us/{0}-latest.osm.pbf'


class Downloader(object):
    """
    Downloads OSM extracts from GeoFabrik in pbf format

    """
    
    def build_url(self, state):
        return US_GEOFABRIK.format(state.replace(' ', '-').lower())

    def download(self, states_file):
        """ For each state in states file build url and download file """
        outfiles = []
        with open(states_file, 'r') as f:
            for state in f.read().splitlines():
                url = self.build_url(state)
                outfiles.append(self._download(url))
        return outfiles

    def _download(self, url):
        """ Dowload file to /tmp """
        filename = url.rsplit('/', 1)[-1]
        tmp = os.path.join('/tmp', filename)
        with open(tmp, 'wb') as f:
            res = requests.get(url, stream=True)
            for block in res.iter_content(1024):
                f.write(block)    
        return tmp
