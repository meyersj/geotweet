Geotweet
========

### License

MIT License. Copyright (c) 2016 Jeffrey Alan Meyers. See `LICENSE.md`


### About

This project contains scripts to retrieve tweets from the Twitter Streaming API and
load into Amazon S3 Buckets. The tweets in S3 are used as input for  Elastic Map Reduce jobs.

Also contains scripts to extract POI nodes from OSM data and load into MongoDB,
as well as loading US states and routes GeoJSON into MongoDB.

### Data Pipeline

Python script running as a daemon will connect to Twitter Streaming API and filter
tweets inside bounding box of Continental US.

For each tweet (if actual Lat-Lon coordinates are included),
extract and marshall some interesting fields as JSON and
append to log file. Log files are rotated every 60 minutes.

+ [Streaming Endpoint](https://dev.twitter.com/streaming/reference/post/statuses/filter)
+ `bin/streamer.py`

Another python script running as a daemon will listen for log file
rotations and upload the archived file to an Amazon S3 Bucket.

+ Run: `bin/s3listener.py` (must set environment variables below)

After log files have been collected for long enough run a Map Reduce
job to count word occurences by each County, State and the entire US.

+ `bin/us-state-county-wordcount-v2.py`


### Environment Variables

The following **environment variables** are required for all the scripts
to run properly

```bash
# ==== For `bin/streamer.py` and `bin/s3listener.py` ====
export GEOTWEET_LOG=/path/to/geotweet.log                   # optional default=/tmp/geotweet.log
export GEOTWEET_STREAM_DIR=/path/to/output/dir              # optional default=/tmp/geotweet
export GEOTWEET_MONGODB_URI="mongodb://127.0.0.1:27017"     # optional default=mongodb://127.0.0.1:27017
# number of minutes in each log file
export GEOTWEET_STREAM_LOG_INTERVAL=60                      # optional default=60  
# =======================================================

# ==== For `bin/streamer.py` ====
# get these from Twitter
export TWITTER_CONSUMER_KEY="..."                           # required
export TWITTER_CONSUMER_SECRET="..."                        # required
export TWITTER_ACCESS_TOKEN_KEY="..."                       # required
export TWITTER_ACCESS_TOKEN_SECRET="..."                    # required
# ===============================

# ==== For `bin/s3listener.py` ====
# get these from AWS
export AWS_ACCESS_KEY_ID="..."                              # required
export AWS_SECRET_ACCESS_KEY="..."                          # required
# you must create this bucket on S3
export AWS_DEFAULT_REGION="region" # example: "us-west-2"   # required
export AWS_BUCKET="already.created.bucket.name"             # required
# =================================
```

### Build VM with MongoDB using Virtualbox

Make sure you have Ubuntu 14.04 (`ubuntu/trusty64`) box installed.

```bash
git clone https://github.com/meyersj/geotweet.git
cd geotweet
vagrant up
```

MongoDB should be accessible at `mongodb://127.0.0.1:27017`.
Make sure all the required **environment variables** are set and the run the scripts

```
vagrant ssh

# load mongo
python /vagrant/bin/loader.py osm /vagrant/data/states.txt  # load OSM POI nodes
python /vagrant/bin/loader.py boundary                      # load State and County GeoJSONs

# run tests
python /vagrant/tests/mongo_tests.py

# Start Twitter-API stream
python /vagrant/bin/streamer.py &

# Listening for log files to load into S3
python /vagrant/bin/s3listener.py &
```

### Dependencies

See `bin/setup.sh` for required dependencies:
+ `java` and `osmosis` must be installed and on your path. [Osmosis Documentation](http://wiki.openstreetmap.org/wiki/Osmosis)
+ MongoDB needs to be installed
+ python `requirements.txt` need to be installed


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


### Twitter API Stream

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
