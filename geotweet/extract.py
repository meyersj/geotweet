import os
import subprocess

POI_TAGS = ["amenity", "builing", "shop", "office", "tourism"]
OSMOSIS_CMD = "osmosis --read-pbf {0} --node-key keyList={1} --write-xml {2}"


class Extractor(object):
    """
    Use `osmosis` to extract POI nodes from an osm file
    
    """
   
    def __init__(self, tags=POI_TAGS):
        self.tags = tags

    def extract(self, source_pbfs, outdir, clean=False):
        extracted = []
        for source in source_pbfs:
            # get filename without the .pbf extension
            fileroot = source.rsplit('/', 1)[-1].rsplit('.', 1)[0]
            target = os.path.join(outdir, fileroot)
            if self._extract(source, target):
                extracted.append(target)
        return extracted

    def _extract(self, source, target):
        key_list = ",".join(self.tags)
        cmd = OSMOSIS_CMD.format(source, key_list, target)
        try:
            subprocess.call(cmd, shell=True)
            return True
        except Exception as e:
            print e
            return False
