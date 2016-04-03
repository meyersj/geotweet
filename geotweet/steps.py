import json

from log import logger, get_rotating_logger


class ProcessStep(object):
    """ Base Class used to build data processing chain """ 
    next_step = None
   
    def get_next(self):
        return self.next_step
    
    def set_next(self, next_step):
        self.next_step = next_step

    def next(self, data):
        if self.next_step:
            return self.next_step.process(data)
        return data

    def process(self, step_input):
        """ Process input and and return output """ 
        return self.next(step_input)


class GeoFilterStep(ProcessStep):
    """
    Process output from Twitter Streaming API
    
    For each record output from the API will be called as argument to process.
    That function will validate and convert tweet to desired format.
    
    """
    def _validate(self, key, record):
        if key in record and record[key]:
            return True
        return False

    def validate_geotweet(self, record):
        """ check that stream record is actual tweet with coordinates """
        if record and  self._validate('user', record) \
                and self._validate('coordinates', record):
            return True
        return False

    def process(self, tweet):
        """ Passes on tweet if missing 'geo' or 'user' property """
        if self.validate_geotweet(tweet):
            return self.next(tweet)
        return None


class ExtractStep(ProcessStep):
    """ Extract interesting fields from Tweet """
    
    def process(self, tweet):
        if not tweet:
            return None
        user = tweet['user']
        data = dict(
            user_id=user['id'],
            name=user['name'],
            screen_name=user['screen_name'],
            description=user['description'],
            location=user['location'],
            friends_count=user['friends_count'],
            followers_count=user['followers_count'],
            tweet_id=tweet['id_str'],
            source=tweet['source'],
            created_at=tweet['created_at'],
            timestamp=tweet['timestamp_ms'],
            lonlat=tweet['coordinates']['coordinates']
        )
        return self.next(data)


class LogStep(ProcessStep):
    """ Log tweet to rotating log """

    def __init__(self, logfile, log_interval=60, when="M"):
        if logfile:
            self.rotating_logger = get_rotating_logger(logfile, log_interval)

    def process(self, tweet):
        if tweet:
            self.rotating_logger.info(json.dumps(tweet))
            return self.next(tweet) 
