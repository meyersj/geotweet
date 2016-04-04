import os
import re

from reader import FileReader


# Reference files to be downloaded from S3
AWS_BUCKET = "https://s3-us-west-2.amazonaws.com/jeffrey.alan.meyers.bucket"
STOPWORDS_LIST_URL = os.path.join(AWS_BUCKET, "geotweet/stopwords.txt")
# use local files if these environment variables are set with a valid filepath
try:
    STOPWORDS_LIST = os.environ['STOPWORDS_LIST_LOCAL']
except KeyError:
    STOPWORDS_LIST = STOPWORDS_LIST_URL


class WordExtractor(FileReader):
    """
    Extract words from a tweet.

    If a provided `src` keyword param references a local file or remote resource
    containing list of stop words, the will be download and used to exclude
    extracted words
    
    """
    def __init__(self, src=STOPWORDS_LIST):
        self.sub_all = re.compile("""[#.!?,"(){}[\]|]|&amp;""")
        self.sub_ends = re.compile("""^[@\\\/~]*|[\\\/:~]*$""")
        self.stopwords = {}
        if src:
            if not self.is_valid_src(src):
                error = "Arg src=< {0} > is invalid."
                error += " Must be existing file or url that starts with 'http'"
                raise ValueError(error.format(src))
            words = self.read(src)
            for word in words.splitlines():
                    self.stopwords[word] = ""

    def clean_unicode(self, line):
        chars = [char for char in line.lower()]
        only_ascii = lambda char: char if ord(char) < 128 else ''
        return str(''.join(filter(only_ascii, chars)))

    def clean_punctuation(self, word):
        return self.sub_ends.sub('', self.sub_all.sub('', word))

    def run(self, line):
        """
        Extract words from tweet

        1. Remove non-ascii characters
        2. Split line into individual words
        3. Clean up puncuation characters
        
        """
        words = []
        for word in self.clean_unicode(line.lower()).split():
            if word.startswith('http'):
                continue
            cleaned = self.clean_punctuation(word)
            if len(cleaned) > 1 and cleaned not in self.stopwords:
                words.append(cleaned)
        return words
