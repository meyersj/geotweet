#!python
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from geotweet.log import logger
from geotweet.stream import TwitterStream, LogTweetHandler


LOG_DIR = os.getenv("GEOTWEET_STREAM_DIR", "/tmp/geotweet")
INTERVAL = int(os.getenv("GEOTWEET_STREAM_LOG_INTERVAL", 5))
# Bounding Boxes
# [Lon,Lat SW corner, Lon,Lat NE corner]
PORTLAND = ["-123.784828,44.683842", "-121.651703,46.188969"]
US = ["-125.0011,24.9493", "-66.9326,49.5904"]
LOCATIONS = US


try:
    os.mkdir(LOG_DIR)
except:
    pass


def main():
    log = os.path.join(LOG_DIR, 'twitter-stream.log')
    
    logger.info("Starting Twitter Streaming API")
    logger.info("Streaming to output log: {0}".format(log))
    logger.info("Log Interval (min): {0}".format(INTERVAL))
    logger.info("Bounding Box: {0}".format(LOCATIONS))

    handler = LogTweetHandler(log, interval=INTERVAL)
    stream = TwitterStream()
    stream.start(handler, locations=LOCATIONS)


if __name__ == "__main__":
    main()
