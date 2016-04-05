import json


class GeoJSONLoader(object):

    def load(self, json_file, load_func):
        with open(json_file, 'r') as f:
            data = json.loads(f.read().decode('latin-1').encode('utf-8'))
            for feature in data['features']:
                load_func(feature)
