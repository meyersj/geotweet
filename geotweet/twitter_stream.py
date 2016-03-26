import os
import sys
import logging
import json
from logging.handlers import TimedRotatingFileHandler

import twitter

from log import logger, get_rotating_logger


LOG_DIR = os.getenv("GEOTWEET_STREAM_DIR", "/tmp/geotweet")
# Bounding Boxes
# [Lon,Lat SW corner, Lon,Lat NE corner]
PORTLAND = ["-123.784828,44.683842", "-121.651703,46.188969"]
US = ["-125.0011,24.9493", "-66.9326,49.5904"]
LOCATIONS = US
INTERVAL = int(os.getenv("GEOTWEET_STREAM_LOG_INTERVAL", 60))

try:
    os.mkdir(LOG_DIR)
except:
    pass


def main():
    log = os.path.join(LOG_DIR, 'twitter-stream.log')
    
    logger.info("Starting Twitter Streaming API")
    logger.info("Streaming to output log: {0}".format(log))
    logger.info("Log Interval (min): {0}".format(INTERVAL))

    handler = LogTweetHandler(log, interval=INTERVAL)
    stream = TwitterStream()
    stream.start(handler, locations=LOCATIONS)


class TwitterClient(object):
    
    def __init__(self):
        try:
            self.api = twitter.Api(
                consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
                consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
                access_token_key=os.getenv('TWITTER_ACCESS_TOKEN_KEY'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.api.VerifyCredentials()
        except twitter.error.TwitterError as e:
            logger.error("Error connecting to twitter API")
            sys.exit(1)


class LogTweetHandler(object):

    def __init__(self, logfile, interval=60, when="M"):
        """ interval is number of minutes for each log file """
        self.logger = get_rotating_logger(logfile, interval)
        self.logfile = logfile

    def _validate(self, key, record):
        if key in record and record[key]:
            return True
        return False
   
    def validate_geotweet(self, record):
        """ check that stream record is actual tweet with coordinates """
        return self._validate('user', record) and self._validate('geo', record)

    def handle(self, record):
        """ called when a record is received from the Twitter API stream """
        if self.validate_geotweet(record):
            tweet = Tweet(record)
            self.logger.info(tweet.as_json())


class TwitterStream(object):
    
    ENVVARS = [
        "TWITTER_CONSUMER_KEY",
        "TWITTER_CONSUMER_SECRET",
        "TWITTER_ACCESS_TOKEN_KEY",
        "TWITTER_ACCESS_TOKEN_SECRET"
    ]

    def __init__(self):
        self.validate_envvar()                        
        self.api = TwitterClient().api

    def validate_envvar(self):
        error = "Error: Make sure following environment variables are set\n"
        error += "\t" + "\n\t".join(self.ENVVARS) + "\n"
        for env in self.ENVVARS:
            if not os.getenv(env, None):
                value = "environment variable {0} not set".format(env)
                logger.error(value)
                raise EnvironmentError(value)
    
    def start(self, handler, locations=PORTLAND):
        try:
            for record in self.api.GetStreamFilter(locations=locations):
                handler.handle(record)
        except Exception as e:
            print e
            logger.error(e)
            sys.exit(1)
           

class Tweet(object):

    def __init__(self, record):
        self.extract_user(record['user'])
        self.extract_meta(record)
        self.record = record

    def extract_user(self, user):
        self.user_id = user['id']
        self.name = user['name']
        self.screen_name = user['screen_name']
        self.description = user['description']
        self.location = user['location']
        self.friends_count = user['friends_count']
        self.followers_count = user['followers_count']

    def extract_meta(self, tweet):
        self.tweet_id = tweet['id_str']
        self.source = tweet['source']
        self.created_at = tweet['created_at']
        self.timestamp = tweet['timestamp_ms']
        self.lonlat = tweet['coordinates']['coordinates']
  
    def as_json(self):
        return json.dumps(dict(
            user_id=self.user_id, name=self.name, screen_name=self.screen_name,
            description=self.description, location=self.location,
            friends_count=self.friends_count, followers_count=self.followers_count,
            tweet_id=self.tweet_id, source=self.source, created_at=self.created_at,
            timestamp=self.timestamp, lonlat=self.lonlat,
            text=self.record['text']
        ))

    def display(self):
        print self.user_id
        print self.name
        print self.screen_name
        print self.description
        print self.location
        print "TWEET"
        print self.created_at, self.timestamp
        print "GEO", self.lonlat
        print self.source
        print self.record['text']


if __name__ == "__main__":
    main()
