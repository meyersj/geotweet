import unittest
import os
from os.path import dirname
import sys

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


MONGODB_URI = os.getenv('GEOTWEET_MONGODB_URI', 'mongodb://127.0.0.1:27017')
PORTLAND = [-122.675983, 45.524764]
PROVIDENCE = [-71.404823, 41.827730]
JOHN_HAY = "John Hay Library"

TIMEOUT = 1 * 1000

def check_connection():
    timeout = TIMEOUT
    args = dict(
        connect=False,
        connectTimeoutMS=timeout,
        socketTimeoutMS=timeout,
        serverSelectionTimeoutMS=timeout
    )   
    try:
        m = MongoClient(MONGODB_URI, **args)
        m.database_names()
        return True
    except ServerSelectionTimeoutError:
        return False
    return False


class ConnectionTestCase(unittest.TestCase):

    def test_connection(self):
        error = "Failed to connect to Mongo Instance < {0} >".format(MONGODB_URI)
        self.assertTrue(check_connection(), error)


if __name__ == "__main__":
    unittest.main()
