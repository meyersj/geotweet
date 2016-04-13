import os
import sys
import time

import twitter as twitter

import logging


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
            logging.error("Error connecting to twitter API " + str(e))
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
                logging.error(value)
                raise EnvironmentError(value)
    
    def stream(self, streamer, process_step=None, timeout=0):
        if timeout:
            stop = time.time() + timeout
        for record in streamer:
            if timeout and time.time() > stop:
                break
            if process_step:
                process_step.process(record)
            else:
                logging.info(json.dumps(record))

    def start(self, process_step=None, timeout=0, locations=None):
        if locations:
            streamer = self.api.GetStreamFilter(locations=locations)
        else:
            streamer = self.api.GetStreamSample()
        self.stream(streamer, process_step=process_step, timeout=timeout)
