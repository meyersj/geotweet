import sys
import os
import urllib2


class FileReader(object):
    """ Read file from the local file system or remote url """

    def is_url(self, src):
        return src.startswith('http')

    def is_valid_src(self, src):
        return os.path.isfile(src) or self.is_url(src)

    def read(self, src):
        """ Download GeoJSON file of US counties from url (S3 bucket) """
        geojson = None
        if not self.is_valid_src(src):
            error = "File < {0} > does not exists or does start with 'http'."
            raise ValueError(error.format(src))
        if not self.is_url(src):
            return open(src, 'r').read().decode('latin-1').encode('utf-8')
        response = urllib2.urlopen(src)
        return response.read().decode('latin-1').encode('utf-8')
