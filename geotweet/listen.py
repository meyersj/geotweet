import os
import sys
import pyinotify

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.log import logger
from geotweet.load import S3Loader


class LogListener(object):
    
    def __init__(self, args):
        """
        Listen for changes to files in log_dir

        When TwitterStream rotates a log the event handler will be called
        The LogEventS3Handler will load the log file into a s3 bucket on AWS
        """
        self.log_dir = args.log_dir
        wm = pyinotify.WatchManager()
        handler = LogEventHandler(bucket=args.bucket, region=args.region)
        self.notifier = pyinotify.Notifier(wm, handler)
        wm.add_watch(self.log_dir, pyinotify.ALL_EVENTS)

    def start(self):
        msg = "Start listening for events in directory: {0}"
        logger.info(msg.format(self.log_dir))
        self.notifier.loop()


class LogEventHandler(pyinotify.ProcessEvent):
    
    def my_init(self, bucket=None, region=None):
        """
        This is automatically called from ProcessEvent.__init__()
        """
        self.bucket = bucket
        self.s3 = S3Loader(bucket, region)
        try:
            self.s3.valid()
        except EnvironmentError as e:
            logger.error(e)
            sys.exit(1)

    def process_IN_MOVED_TO(self, event):
        """
        Log file was rotated. Send to s3
        """
        logger.debug("MOVED LOG {0} {1}".format(event.maskname, event.pathname))
        if self.s3:
            log = "Loading to S3 bucket {0}: {1}".format(self.bucket, event.pathname)
            logger.info(log)
            self.s3.store(event.pathname)
            logger.info("Finished loading: {0}".format(event.pathname))
