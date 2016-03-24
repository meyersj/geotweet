import os
import sys

import twitter

from mongo import MongoQuery


# Bounding Boxes
# [Lon,Lat SW corner, Lon,Lat NE corner]
PORTLAND = ["-123.784828,44.683842", "-121.651703,46.188969"]
US = ["-125.0011,24.9493", "-66.9326,49.5904"]

TWITTER_ENVVAR = [
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN_KEY",
    "TWITTER_ACCESS_TOKEN_SECRET"
]


def main():
    handler = TweetHandler()
    handler.add_step(InitialProcessStep())
    handler.add_step(GeoSearchStep(MongoQuery()))
    handler.add_step(TimelineStep())
    stream = TwitterStream()
    stream.start(handler.handle, locations=PORTLAND)


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
            print e, "\nError connecting to twitter API\n"
            sys.exit(1)


class TweetHandler(object):

    def __init__(self):
        self.steps = []

    def add_step(self, handler):
        self.steps.append(handler)

    def handle(self, record):
        for step in self.steps:
            if record:
                record = step.run(record)
        return record

class InitialProcessStep(object):
    """ Run initial processing on status received from stream """
    def run(self, record):
        tweet = Tweet(record)
        tweet.display()
        print "- - -"
        return tweet


class GeoSearchStep(object):
    
    def __init__(self, mongo):
        self.mongo = mongo
    
    def run(self, record):
        print "SEARCH"
        lonlat = record.lonlat
        for t in self.mongo.find(query=self.mongo.near_query(lonlat, 20)):
            print t
        print "/ / /"
        return record


class TimelineStep(object):
    
    def __init__(self):
        self.api = TwitterClient().api
    
    def run(self, record):
        print "TIMELINE USER", record.user_id
        for status in self.api.GetUserTimeline(record.user_id, count=200):
            status = status.AsDict()
            if "geo" in status:
                tweet = Tweet(status)
                print "\t", tweet.name
                print "\t", tweet.created_at
                print "\t", tweet.lonlat
                print "\t", tweet.record['text']
                print
        print ". . ."
        return record

class TwitterStream(object):

    def __init__(self):
        self.validate_envvar()                        
        self.api = TwitterClient().api

    def validate_envvar(self):
        error = "Error: Make sure following environment variables are set\n"
        error += "\t" + "\n\t".join(TWITTER_ENVVAR) + "\n"
        for env in TWITTER_ENVVAR:
            if not os.getenv(env, None):
                print error
                value = "environment variable {0} not set".format(env)
                raise EnvironmentError(value)
    
    def _validate(self, key, record):
        if key in record and record[key]:
            return True
        return False
   
    def validate_geotweet(self, record):
        return self._validate('user', record) and self._validate('geo', record)
    
    def start(self, handler, locations=PORTLAND):
        for record in self.api.GetStreamFilter(locations=locations):
            if self.validate_geotweet(record):
                handler(record)


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
        #self.tweet_id = tweet['id_str']
        self.source = tweet['source']
        self.created_at = tweet['created_at']
        self.timestamp = tweet['timestamp_ms']
        self.lonlat = tweet['coordinates']['coordinates']
    
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
