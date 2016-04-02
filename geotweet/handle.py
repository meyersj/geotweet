import os
import sys
import json


from log import logger, get_rotating_logger


class LogTweetHandler(object):

    def __init__(self, logfile=None, interval=60, when="M"):
        """ interval is number of minutes for each log file """
        if logfile:
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
