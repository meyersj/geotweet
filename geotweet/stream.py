import os
import sys
import time

import twitter

from log import logger


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
            logger.error("Error connecting to twitter API " + str(e))
            sys.exit(1)


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
    
    def stream(self, streamer, handler, timeout):
        if timeout:
            stop = time.time() + timeout
        for record in streamer:
            if timeout and time.time() > stop:
                break
            handler.handle(record)

    def start(self, handler, timeout=0, locations=None):
        if locations:
            streamer = self.api.GetStreamFilter(locations=locations)
        else:
            streamer = self.api.GetStreamSample()
        self.stream(streamer, handler, timeout)
