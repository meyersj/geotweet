import sys

import pyinotify

from load import S3Loader
from log import logger


BUCKET = "jeffrey.alan.meyers.geotweet"
LOG_DIR = os.getenv("GEOTWEET_STREAM_DIR", "/tmp/geotweet")


class LogEventS3Handler(pyinotify.ProcessEvent):
    
    def my_init(self, s3=S3Loader()):
        """
        This is automatically called from ProcessEvent.__init__()
        """
        try:
            s3.valid()
            self.s3 = s3
        except EnvironmentError as e:
            print e

    def process_IN_MOVED_TO(self, event):
        """
        Log file was rotated. Send to s3
        """
        logger.debug("MOVED LOG {0} {1}".format(event.maskname, event.pathname))
        if self.s3:
            logger.info("Loading to S3 bucket {0}: {1}".format(BUCKET, event.pathname))
            self.s3.store(BUCKET, event.pathname)
            logger.info("Finished loading: {0}".format(event.pathname))


class LogListener(object):
    
    def __init__(self, log_dir=LOG_DIR):
        wm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(wm, LogEventS3Handler())
        self.log_dir = log_dir
        wm.add_watch(self.log_dir, pyinotify.ALL_EVENTS)

    def start(self):
        logger.info("Start listening for events in directory: {0}".format(self.log_dir))
        self.notifier.loop()
    

if __name__ == "__main__":
    LogListener().start()
