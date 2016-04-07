Geotweet
========

### License

MIT License. Copyright (c) 2016 Jeffrey Alan Meyers. See `LICENSE.md`


### About

This project contains code to log tweets from the
[Twitter Streaming API](https://dev.twitter.com/streaming/reference/post/statuses/filter)
and load them into Amazon S3 Buckets.
The log files in S3 are then used as input for Elastic MapReduce jobs.


### Install

Dependencies
```bash
apt-get update
apt-get install python-dev \
    libgeos-dev libspatialindex- \
    build-essential protobuf-compiler libprotobuf-dev

# if you don't already have pip
curl https://bootstrap.pypa.io/get-pip.py | python
```

Install `geotweet` command line utility
```bash
pip install geotweet
```

Installing this package will provide you with a python executable named `geotweet`.

### Usage

```bash
geotweet stream|load|geomongo|osm [options]
geotweet stream --help                  # store Twitter Streaming API to log files
geotweet load --help                    # load log files to S3 bucket
geotweet geomongo --help                # load GeoJSON files into MongoDB instance
geotweet osm --help                     # download osm extracts from geofabrik
                                        # extract POI nodes and load into S3 bucket
```

#### stream

Store geograhpic tweets from Twitter Streaming API into `--log-dir`
```
usage: geotweet stream [-h] [--log-dir LOG_DIR] [--log-interval LOG_INTERVAL]
                       [--bbox BBOX]

optional arguments:
  -h, --help            show this help message and exit
  --log-dir LOG_DIR     Path to log file directory
  --log-interval LOG_INTERVAL
                        Minutes in each log file
  --bbox BBOX           Bounding Box as 'SW,NE' using 'Lon,Lat' for each
                        point.
```

#### load

Listen for archived files in `--log-dir` and upload to S3 bucket
```
usage: geotweet load [-h] [--log-dir LOG_DIR] [--bucket BUCKET]
                     [--region REGION]

optional arguments:
  -h, --help         show this help message and exit
  --log-dir LOG_DIR  Path to log file directory
  --bucket BUCKET    AWS S3 Bucket name
  --region REGION    AWS S3 Region such as 'us-west-2'
```

#### geomongo

Load GeoJSON files into MongoDB
```
usage: geotweet geomongo [-h] [--mongo MONGO] [--db DB] file collection

positional arguments:
  file           Path to geojson file
  collection     Name of collection

optional arguments:
  -h, --help     show this help message and exit
  --mongo MONGO  MongodDB URI (default=mongodb://127.0.0.1:27017)
  --db DB        Name of db (default=geotweet)
```

#### osm

Download OSM extracts from GeoFabrik, extract POI nodes and load to S3 Bucket
```
usage: geotweet osm [-h] [--output OUTPUT] [--states STATES] [--bucket BUCKET]
                    [--region REGION]

optional arguments:
  -h, --help       show this help message and exit
  --output OUTPUT  Location of output files (default=/tmp)
  --states STATES  File containing list of states to download and load
  --bucket BUCKET  AWS S3 Bucket name
  --region REGION  AWS S3 Region such as 'us-west-2'
```

#### Environment Variables

For `geotweet stream` the following environment variables must be set.
See `example_conf/stream-envvars.sh` for all options.
+ `TWITTER_CONSUMER_KEY`
+ `TWITTER_CONSUMER_SECRET`
+ `TWITTER_ACCESS_TOKEN_KEY`
+ `TWITTER_ACCESS_TOKEN_SECRET`

For `geotweet load` the following environment variables must be set.
See `example_conf/load-envvars.sh` for all options.
+ `AWS_ACCESS_KEY_ID`
+ `AWS_SECRET_ACCESS_KEY`
+ `AWS_BUCKET` (if not provided as cli param)
+ `AWS_DEFAULT_REGION` (if not provided as cli param)


#### Example

```
pip install geotweet

# Twitter
export TWITTER_CONSUMER_KEY="..."
export TWITTER_CONSUMER_SECRET="..."
export TWITTER_ACCESS_TOKEN_KEY="..."
export TWITTER_ACCESS_TOKEN_SECRET="..."

# AWS
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# start streaming to log files rotate log file every 5 minutes
geotweet stream --log-dir /tmp/geotweet --log-interval 5 &  

# start loading archived log rotations to S3
geotweet load --log-dir /tmp/geotweet --bucket already.created.bucket --region us-west-2 &
```

To run as daemon on Ubuntu with Upstart copy
`example_conf/geotweet-stream.conf` and `example_conf/geotweet-load.conf`
to `/etc/init` and set the environment variables in those files then run:
```
sudo service geotweet-stream start
sudo service geotweet-load start
```

### Data Pipeline

#### 1. Extract Geographic Tweets

Run ```geotweet stream```

Python script running on a cheap VPS (DigitalOcean) will connect to the
*Twitter Streaming API* and filter for tweets inside Continental US.

For each tweet (if Lat-Lon coordinates are provided),
extract fields, marshal as JSON and append to a log file.
The log files are rotated every 60 minutes.

Example of log entry (1 line with pretty print)
```
{
   "source" : "<a href=\"http://www.tweet3po.org\" rel=\"nofollow\">Tweet3po</a>",
   "followers_count" : 959,
   "screen_name" : "Tweet3po",
   "tweet_id" : "712897292534087681",
   "friends_count" : 5,
   "location" : "Orlando, FL",
   "timestamp" : "1458802934188",
   "text" : "#HouseBusinessCheck 1750 Mills Ave N 32803 (3/24 02:45) #Orlando #LakeFormosa",
   "created_at" : "Thu Mar 24 07:02:14 +0000 2016",
   "user_id" : 56266341,
   "description" : "Hyper-Local Neighborhood News.",
   "name" : "Tweet3po",
   "lonlat" : [
      -81.36450067,
      28.56774084
   ]
}
```


#### 2. Load Tweets into S3

Run ```geotweet load```

Listen for log file rotations. Each archived file will be uploaded into an Amazon S3 Bucket.


#### 3. Process with EMR

After log files have been collected for long enough run a Map Reduce
job to count word occurences by each County, State and the entire US.

```
git clone https://github.com/meyersj/geotweet.git
cd geotweet
pip install -r requirements.txt
```

Run **Local** Job 1
```bash
# cd /path/to/geotweet
data=$PWD/geotweet/data/mapreduce/twitter-stream.log.2016-03-27_01-53

# move to MapReduce jobs directory
cd geotweet/mapreduce

# Job 1
# --------------------------------
# Map WordCount broken down by US, State and County (Local spatial lookup using Shapely/Rtree)
python state_county_wordcount.py $data

# Output tuples: `((Word, State ID, County ID), Total)`
# (("yesterday", "20", "197"), 30)

 
# Job 2 Requires MongoDB instance)
# ---------------------------------
# MR WordCount broken down by Metro Area
# build local spatial index, persist results to Mongo
# if MongoDB is running at 127.0.0.1:27017
export GEOTWEET_MONGODB_URI="mongodb://127.0.0.1:27017"
python metro_mongo_wordcount.py $data

# Output stored in MongoDB `db=geotweet` as `collection=geotweet` as documents
# {
#   metro_area:   "Portland, OR--WA",
#   word:         "beautiful",
#   count:        142
# }
```


Run **EMR** Job
```bash
# set all of the config parameters, make sure all example paths are corrected
cp example_conf/mrjob.conf ~/.mrjob.conf
vim ~/.mrjob.conf       

# set input/output S3 buckets
src=s3://some.s3.bucket/input                               # folder containing logs from `streamer.py`
dst=s3://some.s3.bucket/output/<new folder>                 # the new folder should not already exist

# start job and supress stdout output (will go to s3) 
python geotweet/mapreduce/state_county_wordcount.py $src -r emr --output-dir=$dst --no-output       
```

### Tests

Tests available to run after cloning and installing dependencies.
```
nosetests geotweet/tests/twitter        # requires environment variables listed above to be set
nosetests geotweet/tests/mapreduce
nosetests geotweet/tests/geomongo       # requires MongoDB instance running locally
```

### Virtual Machine

To build a local virtual machine with MongoDB you need `virtualbox`/`vagrant`
installed and a `ubuntu/trusty64` box
```
git clone https://github.com/meyersj/geotweet.git
cd geotweet
vagrant box add ubuntu/trusty64
vagrant up
vagrant ssh
cd /vagrant   # contains repository

# all packages are already installed
# geotweet executable is on your path
```
