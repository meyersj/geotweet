import os
import sys

import twitter

from mongo import MongoQuery


PORTLAND = ["-123.784828,44.683842", "-121.651703,46.188969"]
TWITTER_ENV = [
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN_KEY",
    "TWITTER_ACCESS_TOKEN_SECRET"
]


def main():
    handler = TweetHandler(MongoQuery())
    stream = Stream()
    stream.start(handler.handle)


class TweetHandler(object):

    def __init__(self, mongo):
        self.mongo = mongo:

    def handle(self, record):
        user = User(record['user'])
        tweet = Tweet(record)
        print user
        print tweet
        print " - - -"
        query = m.near_query(tweet.coordinates["coordinates"], 20)
        for t in m.find(query=query):
            print t
        print "------"
        print


class Stream(object):

    def __init__(self):
        self.validate_env()                        
        self.api = self.get_client()

    def validate_env(self):
        error = "Error: Make sure following environment variables are set\n"
        error += "\t" + "\n\t".join(TWITTER_ENV) + "\n"
        for env in TWITTER_ENV:
            if not os.getenv(env, None):
                print error
                value = "environment variable {0} not set".format(env)
                raise EnvironmentError(value)
    
    def _validate(self, key, record):
        if key in record and record[key]:
            return True
        return False
   
    def validate(self, record):
        return self._validate('user', record) and self._validate('geo', record)

    def get_client(self):
        try:
            api = twitter.Api(
                consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
                consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
                access_token_key=os.getenv('TWITTER_ACCESS_TOKEN_KEY'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            verify = api.VerifyCredentials()
        except twitter.error.TwitterError as e:
            print e, "\nError connecting to twitter API\n"
            sys.exit(1)
        return api

    def start(self, handler):
        for record in self.api.GetStreamFilter(locations=PORTLAND):
            if self.validate(record):
                handler(record)


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


class Tweet(Obj):

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


if __name__ == "__main__":
    main()
