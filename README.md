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

```
pip install geotweet
```

Installing this package will provide you with a python executable named `geotweet`.

### Usage

```
geotweet stream|listen [parameters]
geotweet stream --help
geotweet listen --help
```

#### Usage: stream
```
usage: geotweet stream [-h] [--log-dir LOG_DIR] [--log-interval LOG_INTERVAL]
                       [--bbox BBOX]

optional arguments:
  -h, --help            show this help message and exit
  --log-dir LOG_DIR     Path to log file directoy
  --log-interval LOG_INTERVAL
                        Minutes in each log file
  --bbox BBOX           Bounding Box as 'SW,NE' using 'Lon,Lat' for each point
```

#### Usage: listen
```
usage: geotweet listen [-h] [--log-dir LOG_DIR] [--bucket BUCKET]
                       [--region REGION]

optional arguments:
  -h, --help         show this help message and exit
  --log-dir LOG_DIR  Path to log file directoy
  --bucket BUCKET    AWS S3 Bucket name
 --region REGION    AWS S3 Region such as 'us-west-2'
```

#### Environment Variables

For `geotweet stream` the folloing environment variables must be set
+ `TWITTER_CONSUMER_KEY`
+ `TWITTER_CONSUMER_SECRET`
+ `TWITTER_ACCESS_TOKEN_KEY`
+ `TWITTER_ACCESS_TOKEN_SECRET`

For `geotweet listen` the folloing environment variables must be set
+ `AWS_ACCESS_KEY_ID`
+ `AWS_SECRET_ACCESS_KEY`
+ `AWS_BUCKET` (if not provided as cli param)
+ `AWS_DEFAULT_REGION` (if not provided as cli param)

See `example_conf/streamer_envvars.sh` and `example_conf/s3listener_envvars.sh`.

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

# start streaming to log file
geotweet stream --log-dir /tmp/geotweet --log-interval 5 &  # rotate log file every 5 minutes

# start listening for log rotations and load to S3
geotweet listen --log-dir /tmp/geotweet --bucket already.created.bucket --region us-west-2 &
```

To run as daemon on Ubuntu copy `example_conf/streamer.conf` and `example_conf/s3listener.conf`
to `/etc/init` and set the environment variables then run:
```
sudo service streamer start
sudo service s3listener start
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

Run ```geotweet listen```

Listen for log file rotations. Each archived file will be uploaded into an Amazon S3 Bucket.


#### 3. Process with EMR

After log files have been collected for long enough run a Map Reduce
job to count word occurences by each County, State and the entire US.

```
git clone https://github.com/meyersj/geotweet.git
cd geotweet
sudo pip install -r mapreduce_requirements.txt
nosetests tests/mapreduce
```

Run **Local** Job
```bash
# run geo wordcount job with sample data
python mapreduce/geo.py data/mapreduce/twitter-stream.log.2016-03-26_13-13
```

Run **EMR** Job
```bash
cp example_conf/mrjob.conf ~/.mrjob.conf
vim ~/.mrjob.conf       # set all of the config parameters, make sure all example paths are corrected
src=s3://some.s3.bucket/input                               # folder containing logs from `streamer.py`
dst=s3://some.s3.bucket/output/<new folder>                 # the new folder should not already exist
python mapreduce/geo.py $src -r emr --output-dir=$dst --no-output     # supress output to stdout (will go to s3)   
```

Output tuples have the form `([Word, State, County], Total)`
