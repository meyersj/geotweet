import os
import sys
import json
import argparse

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from stream import TwitterStream
from load import LogListener
from stream_steps import GeoFilterStep, ExtractStep, LogStep

import logging
logger = logging.getLogger(__name__)


# Bounding Box: [Lon,Lat SW corner, Lon,Lat NE corner]
PORTLAND = "-123.784828,44.683842,-121.651703,46.188969"
CONTINENTAL_US = "-125.0011,24.9493,-66.9326,49.5904"

# default parameters from environment variables or set to defaults
DEFAULT_LOG_DIR = "/tmp/geotweet"
DEFAULT_LOG_INTERVAL = 5
DEFAULT_LOCATION = CONTINENTAL_US


class Geotweet(object):
    
    handler = None
    starting_step = None

    def __init__(self, args):
        self.log_dir = args.log_dir if args.log_dir else DEFAULT_LOG_DIR
        try:
            # stream arguments
            self.log_interval = args.log_interval \
                if args.log_interval else DEFAULT_LOG_INTERVAL
            self.bbox = self.build_bbox(args.bbox if args.bbox else CONTINENTAL_US)
        except AttributeError:
            pass
        try:
            # listen arguments
            self.bucket = args.bucket
            self.region = args.region
        except AttributeError:
            pass
    
    def build_bbox(self, bbox):
        if not bbox:
            return None
        # build bounding box from bbox argument
        coords = [ coord.strip() for coord in bbox.split(',') ]
        if len(coords) != 4:
            error = "--bbox must be in the form 'sw-x,sw-y,ne-x,ne-y'"
            raise ValueError(error.format(bbox))
        return [coords[0] + "," + coords[1], coords[2] + "," + coords[3]]

    def add_step(self, step):
        if not self.starting_step:
            self.starting_step = step
            return
        tmp = self.starting_step
        while tmp.get_next():
            tmp = tmp.get_next()
        else:
            tmp.set_next(step)
   
    def stream(self):
        try:
            os.mkdir(self.log_dir)
        except OSError:
            msg = "Output log directory < {0} > already exists".format(self.log_dir)
            logger.debug(msg)
        log = os.path.join(self.log_dir, 'twitter-stream.log')
        logger.info("Starting Twitter Streaming API")
        logger.info("Streaming to output log: {0}".format(log))
        logger.info("Log Interval (min): {0}".format(self.log_interval))
        logger.info("Bounding Box: {0}".format(self.bbox))
        # initialize processing step chain
        self.add_step(GeoFilterStep())
        self.add_step(ExtractStep())
        self.add_step(LogStep(logfile=log, log_interval=self.log_interval))
        # start Twitter Streaming API (does not return)
        TwitterStream().start(process_step=self.starting_step, locations=self.bbox)

    def load(self):
        msg = "Start listening for events in directory: {0}"
        logger.info(msg.format(self.log_dir))
        logger.info("AWS Bucket: {0}".format(self.bucket))
        logger.info("AWS Region: {0}".format(self.region))
        # start listener (does not return)
        LogListener(self.log_dir, self.bucket, self.region).start()
