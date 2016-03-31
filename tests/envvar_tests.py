import unittest
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.load import S3Loader


STREAMER_ENVVARS = [
    'TWITTER_CONSUMER_KEY',
    'TWITTER_CONSUMER_SECRET',
    'TWITTER_ACCESS_TOKEN_KEY',
    'TWITTER_ACCESS_TOKEN_SECRET',
]

S3LISTENER_ENVVARS = [
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_DEFAULT_REGION',
    'AWS_BUCKET',
]


class StreamerEnvvarTests(unittest.TestCase):
    
    def test_envvars(self):
        envvars = STREAMER_ENVVARS
        for required in envvars:
            error = "streamer.py environment variable error\n"
            error += "Environment Variable: < {0} > not set\n"
            error += "These all must be set < {1} >"
            env = os.getenv(required)
            self.assertIsNotNone(env, error.format(required, envvars))


class S3ListenerEnvvarTests(unittest.TestCase):
    
    def test_envvars(self):
        envvars = S3LISTENER_ENVVARS
        for required in envvars:
            error = "s3listener.py environment variable error\n"
            error += "Environment Variable: < {0} > not set\n"
            error += "These all must be set < {1} >"
            env = os.getenv(required)
            self.assertIsNotNone(env, error.format(required, envvars))

if __name__ == "__main__":
    unittest.main()
