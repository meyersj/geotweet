import os

import boto3


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
