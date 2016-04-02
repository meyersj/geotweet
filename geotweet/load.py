import os
import json

from lxml.etree import iterparse
import boto3


class GeoJSONLoader(object):

    def load(self, json_file, load_func):
        with open(json_file, 'r') as f:
            data = json.loads(f.read().decode('latin-1').encode('utf-8'))
            for feature in data['features']:
                load_func(feature)
        

class OSMLoader(object):
    """
    Process osm files containing POI nodes

    """

    def load(self, poi_files, load_func):
        for poi in poi_files:
            self._load(poi, load_func)

    def _build_data(self, elem):
        data = dict(elem.attrib)
        data["properties"] = self._get_tags(elem)
        data["geometry"] = {
            "type":"Point",
            "coordinates":[float(data["lon"]), float(data["lat"])]
        }
        data["_id"] = data["id"]
        del data["lat"]
        del data["lon"]
        return data

    def _load(self, poi, load_func):
        for event, elem in iterparse(poi):
            # if a node contains any POI tags grab them and append
            # node and tags as json to output file
            if elem.tag == "node":
                # call load function with data (usually write to database)
                data = self._build_data(elem)
                load_func(data)

            # subtree has been fully processed so clear from memory
            if elem.tag in ["node", "way", "relation"]:
                elem.clear()

    def _get_tags(self, elem):
        tags = {}
        for child in list(elem):
            key = child.attrib.get('k')
            if child.tag == "tag":
                tags[key] = child.attrib.get('v')
        return tags


class S3Loader(object):
    
    envvars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']

    def __init__(self, bucket=None, region=None):
        self.bucket = bucket
        if region:
            os.environ['AWS_DEFAULT_REGION'] = region
    
    def valid(self):
        if not self.bucket:
            error = "Error: AWS Bucket not set"
            raise ValueError(error)
        for envvar in self.envvars:
            if not os.getenv(envvar):
                error = "Error: Environment variable {0} not set".format(envvar)
                raise EnvironmentError(error)

    def store(self, filepath):
        if not self.bucket:
            return False
        filename = filepath.rsplit('/', 1)[-1]
        s3 = boto3.resource('s3')
        s3.Object(self.bucket, filename).put(Body=open(filepath, 'rb'))
