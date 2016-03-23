import os
import sys
import pprint

import twitter
import time

pp = pprint.PrettyPrinter(indent=4)
portland = "-123.784828,44.683842,-121.651703,46.188969 "


def validate(key, record):
    if key in record and record[key]:
        return True
    return False


class Connect(object):

    def __init__(self):
        self.consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        self.consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        self.access_token_key = os.getenv('TWITTER_ACCESS_TOKEN_KEY')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    def client(self):
        try:
            api = twitter.Api(
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token_key=self.access_token_key,
                access_token_secret=self.access_token_secret
            )
            verify = api.VerifyCredentials()
        except twitter.error.TwitterError as e:
            print "Error connecting to twitter API"
            print "Make sure following environment variables are set"
            print "\tTWITTER_CONSUMER_KEY"
            print "\tTWITTER_CONSUMER_SECRET"
            print "\tTWITTER_ACCESS_TOKEN_KEY"
            print "\tTWITTER_ACCESS_TOKEN_SECRET"
            sys.exit(1)
        return api


class Obj(object):
   
    def _display(self, ident, data, line_end=True):
        try:
            data = str(data) if data else ""    
        except UnicodeEncodeError:
            data = ""    
        line = "{0}: {1}".format(ident, data)
        if line_end:
            return line + "\n"
        return line


class User(Obj):

    def __init__(self, user):
        self.user_id = user['id']
        self.name = user['name']
        self.screen_name = user['screen_name']
        self.description = user['description']
        self.location = user['location']
        self.friends_count = user['friends_count']
        self.followers_count = user['followers_count']

    def __repr__(self):
        ret = self._display("ID", self.user_id)
        ret += self._display("User", self.name)
        ret += self._display("Screen Name", self.screen_name)
        ret += self._display("Description", self.description)
        ret += self._display("Location", self.location)
        ret += self._display("Friends Count", self.friends_count)
        ret += self._display("Followers Count", self.followers_count, line_end=False)
        return ret


class GeoTweet(Obj):

    def __init__(self, tweet):
        self.tweet_id = tweet['id_str']
        self.text = tweet['text']
        self.source = tweet['source']
        self.created_at = tweet['created_at']
        self.timestamp = tweet['timestamp_ms']
        self.coordinates = tweet['coordinates']
    
    def __repr__(self):
        ret = self._display("ID", self.tweet_id)
        ret += self._display("Created At", self.created_at)
        ret += self._display("Timestamp", self.timestamp)
        ret += self._display("Coordinates", self.coordinates)
        ret += self._display("Source", self.source)
        try:
            ret += "Text:\n\n" + str(self.text)
        except UnicodeEncodeError:
            ret += "Text:\n\n"
        return ret


class Runner(object):

    @staticmethod
    def location_stream(api, locations):
        for record in api.GetStreamFilter(locations=locations):
            if validate('user', record) and validate('geo', record):
                user = User(record['user'])
                print user
                print
                #pp.pprint(record)
                tweet = GeoTweet(record)
                print tweet
                geo_tweets = Runner.user_stream(api, record['user']['id'])
                print "-------"
                #print

    @staticmethod
    def user_stream(api, user_id):
        for record in api.GetUserTimeline(user_id=user_id):
            if record.coordinates:
                print "\t", record.created_at
                print "\t", record.text
                print "\t", record.coordinates
                print

def stream():
    api = Connect().client()
    if api:
        Runner.location_stream(api, [portland])

if __name__ == "__main__":
    stream()
