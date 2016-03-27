Geotweet
========


This project contains scripts to retrieve tweets from the Twitter Streaming API and
load into Amazon S3 Buckets. The intention is the use the tweets in S3 as input to 
Elastic Map Reduce jobs.

Also contains scripts to extract POI nodes from OSM data and load into MongoDB,
as well as loading US states and routes GeoJSON into MongoDB.


### Dependencies

```bash
git clone https://github.com/meyersj/geotweet.git
cd geotweet
pip install -r requirements.txt
```


### Required Environment Variables

The following **environment variables** are required for all the scripts
to run properly

```bash
export GEOTWEET_LOG=/tmp/geotweet.log
export GEOTWEET_STREAM_DIR=/tmp/geotweet
export GEOTWEET_STREAM_LOG_INTERVAL=5   # number of minutes in each log file
export GEOTWEET_MONGODB_URI="mongodb://127.0.0.1:27017"

# get these from Twitter
export TWITTER_CONSUMER_KEY="..."
export TWITTER_CONSUMER_SECRET="..."
export TWITTER_ACCESS_TOKEN_KEY="..."
export TWITTER_ACCESS_TOKEN_SECRET="..."

# get these from AWS
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# you must create this bucket on S3
export AWS_DEFAULT_REGION="region" # example: "us-west-2"
export AWS_BUCKET="already.created.bucket.name"
```


### Load OSM POI Data in MongoDB

Download osm data and extract POI nodes. Load each POI into MongoDB with
spatial index.

**Run**: `python bin/loader.py osm [states.txt]`

Optionally provide a list new line delimited US States.
Defaults to `data/states.txt`

Example:
```txt
Oregon
Washington
California
```

### Load State and County Boundary Data in MongoDB

Load US states and counties boundary geometry as GeoJSON documents
into MongoDB.

**Run**: `python bin/loader.py boundary`


### Twitter Stream

The script `bin/stream.py` will start the Twitter Streaming API and filter for
tweets with coordinates inside a specified bounding box. The default is
Continental US. To change that you can modify the variable `LOCATIONS` inside
`bin/stream.py`.

```py
# File: bin/stream.py

# [Lon,Lat SW corner, Lon,Lat NE corner]
US = ["-125.0011,24.9493", "-66.9326,49.5904"]
LOCATIONS = US
```

The filtered tweets are stored into a log file as json.

**Run**: `python bin/stream.py`


### Amazon S3 Log Listener

The `bin/s3listener.py` script will begin listing to a directory for output from
`twitter_stream.py`. After the `GEOTWEET_STREAM_LOG_INTERVAL` time has elapsed the
file will be renamed with a timestamp to be archived. This script will listen for
that event and then upload the log file to a S3 bucket.


**Run**: `python bin/s3listener.py`


## Run as scripts as service on Ubuntu using upstart scripts

If running on Ubuntu you can set the environment variables in
`example_conf/geotweet.conf` and `example_conf/s3listener.conf`, and copy those
files to `/etc/init/`

To start them as a service run:
```
sudo service geotweet start
sudo service s3listener start
```
