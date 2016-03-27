import logging
from logging.handlers import TimedRotatingFileHandler
import os


LOG_NAME = 'geotweet'
LOG_FILE = os.getenv('GEOTWEET_LOG', '/tmp/geotweet.log')
LOG_LEVEL = logging.DEBUG
TWITTER_LOG_NAME = 'twitter-stream'


def get_logger():
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(LOG_LEVEL)
    fh = logging.FileHandler(LOG_FILE)
    logformat = '%(levelname)s %(pathname)s %(asctime)s: %(message)s'
    formatter = logging.Formatter(logformat)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def get_rotating_logger(logfile, interval, when="M"):
    logger = logging.getLogger(TWITTER_LOG_NAME)
    logger.setLevel(LOG_LEVEL)
    handler = TimedRotatingFileHandler(logfile, when=when, interval=interval)
    logger.addHandler(handler)
    return logger


logger = get_logger()
