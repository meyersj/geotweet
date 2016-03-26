Geotweet
========


This project contains scripts to retrieve tweets from the Twitter Streaming API and load into Amazon S3 Buckets. The intention is the use the tweets in S3 as input to Elastic Map Reduce jobs

Install dependencies
```bash
git clone https://github.com/meyersj/geotweet.git
cd geotweet
virtualenv env
./env/bin/pip install -r requirements.txt
```

### Twitter Stream

The script `geotweet/twitter_stream.py` will start the Twitter Streaming API and filter for tweets with coordinates inside a specified bounding box. The default is Continental US. To change that you can modify the variable `LOCATIONS` inside `twitter_stream.py`.

```py
# File: twitter_stream.py

# [Lon,Lat SW corner, Lon,Lat NE corner]
US = ["-125.0011,24.9493", "-66.9326,49.5904"]
LOCATIONS = US
```

The filtered tweets are stored into a log file as json. The default location is `/tmp'.

You must set the following **environment variables**

```bash
export GEOTWEET_LOG="/var/log/geotweet.log"
export GEOTWEET_STREAM_DIR="/path/to/output" # default /tmp
# number of minutes for each log file
env GEOTWEET_STREAM_LOG_INTERVAL=60  # default 60

# get these from Twitter
export TWITTER_CONSUMER_KEY="..."
export TWITTER_CONSUMER_SECRET="..."
export TWITTER_ACCESS_TOKEN_KEY="..."
export TWITTER_ACCESS_TOKEN_SECRET="..."
```
**Run**: `./env/bin/python geotweet/twitter_stream.py`

## Amazon S3 Listener

The `geotweet/s3listener.py` script will begin listing to a directory for output from `twitter_stream.py`. After the `GEOTWEET_STREAM_LOG_INTERVAL` time has elapsed the file will be renamed with a timestamp to be archived. This script will listen for that event and then upload the log file to a S3 bucket.

You must set the following **environment variables**
```bash
export GEOTWEET_LOG="/var/log/geotweet.log"
export GEOTWEET_STREAM_DIR="/path/to/output" # default /tmp

# Get this from AWS 
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# You must create this bucket on S3
# Specify region for your bucket
export AWS_BUCKET="bucket.name"
export AWS_DEFAULT_REGION="us-west-2"
```

**Run**: `./env/bin/python geotweet/s3listener.py`

## Run as service on Ubuntu using upstart scripts

If running on Ubuntu you can set the environment variables in `example_conf/geotweet.conf` and `example_conf/s3listener.conf`, and copy those files to `/etc/init/`

To start them as a service run:
```
sudo service geotweet start
sudo service s3listener start
```
