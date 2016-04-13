import sys
import os
import urllib2
import hashlib


class FileReader(object):
    """ Read file from the local file system or remote url """

    def is_url(self, src):
        return src.startswith('http')

    def is_valid_src(self, src):
        return os.path.isfile(src) or self.is_url(src)

    def get_location(self, src):
        digest = self.digest(src)
        if not digest:
            return None
        return os.path.join('/tmp', "geotweet-file-{0}".format(digest))

    def digest(self, src):
        if not src or type(src) != str:
            return None
        m = hashlib.md5()
        if self.is_url(src):
            m.update(src)
        else:
            m.update(os.path.abspath(src))
        return m.hexdigest()

    def read(self, src):
        """ Download GeoJSON file of US counties from url (S3 bucket) """
        geojson = None
        if not self.is_valid_src(src):
            error = "File < {0} > does not exists or does start with 'http'."
            raise ValueError(error.format(src))
        if not self.is_url(src):
            return open(src, 'r').read().decode('latin-1').encode('utf-8')
        tmp = self.get_location(src)
        # if src poits to url that was already downloaded
        # read from local file instead
        if os.path.isfile(tmp):
            with open(tmp, 'r') as f:
                return f.read()
        # download file and write to local filesystem before returning
        response = urllib2.urlopen(src)
        data = response.read().decode('latin-1').encode('utf-8')
        with open(tmp, 'w') as f:
            f.write(data)
            return data
