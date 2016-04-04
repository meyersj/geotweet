import os
import sys
import glob
import time
import shutil

import boto3

import logging
logger = logging.getLogger(__name__)


POLL_INTERVAL = 60


class LogListener(object):
    
    def __init__(self, log_dir, bucket, region, remove=False, poll=POLL_INTERVAL):
        """
        Listen for changes to files in log_dir

        When TwitterStream rotates a log the event handler will be called
        The LogEventS3Handler will load the log file into a s3 bucket on AWS
        """
        self.log_dir = log_dir
        self.bucket = bucket
        self.s3 = S3Loader(bucket, region)
        self.poll = poll
        self.remove = remove
        try:
            self.s3.valid()
        except EnvironmentError as e:
            logger.error(e)
            sys.exit(1)

    def start(self):
        if not os.path.isdir(self.log_dir):
            msg = "Directory < {0} > does not exist".format(self.log_dir)
            logger.error(msg)
            sys.exit(1)

        pattern = 'twitter-stream.log.*'
        while True:
            for log in glob.glob(os.path.join(self.log_dir, pattern)):
                self.load(log)
            time.sleep(self.poll)

    def load(self, log):
        if not self.s3:
            return
        msg = "Loading {0} to S3 bucket {1}".format(log, self.bucket)
        logger.info(msg)
        self.s3.store(log)
        logger.info("Success loading {0}".format(log))
        self.archive(log)

    def archive(self, log):
        if not self.remove:
            filepath = os.path.dirname(log)
            filename = os.path.basename(log)
            archive = os.path.join(filepath, 'loaded.{0}'.format(filename))
            logger.info("Archiving {0} to {1}".format(log, archive))
            shutil.copyfile(log, archive)
        logger.info("Removing log file {0}".format(log))
        os.remove(log)


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
