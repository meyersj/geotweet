Geotweet
========

### License

MIT License. Copyright (c) 2016 Jeffrey Alan Meyers. See `LICENSE.md`


### About

This project contains python scripts to log tweets from the
[Twitter Streaming API](https://dev.twitter.com/streaming/reference/post/statuses/filter)
and load them into Amazon S3 Buckets.
The log files in S3 are then used as input for Elastic Map Reduce jobs.

Also contains some *(retired)* scripts to extract POI nodes from OSM data and
load into MongoDB, as well as loading US states and routes GeoJSON into MongoDB.

### Data Pipeline

#### 1. Extract Geographic Tweets **(Daemon)**

Python script running on a cheap VPS (DigitalOcean) will connect to the
*Twitter Streaming API* and filter for tweets inside Continental US.

For each tweet (if Lat-Lon coordinates are provided),
extract fields, marshal as JSON and append to a log file.
The log files are rotated every 60 minutes.

+ `python bin/streamer.py`
+ See `example_conf/streamer_envvars.sh`. Required environment variables to run `streamer.py`
+ See `example_conf/streamer.conf`. Upstart script to run as Daemon on Ubuntu

#### 2. Load Tweets into S3 **(Daemon)**

Another python script will be listening for the `streamer.py` log file rotations.
Each archived file will be uploaded into an Amazon S3 Bucket.

+ `python bin/s3listener.py`
+ See `example_conf/s3listener_envvars.sh` for the required environment variables to run `s3listener.py`
+ See `example_conf/s3listener.conf` for an Upstart script to run as Daemon on Ubuntu


#### 3. Process with EMR **(Batch)**

After log files have been collected for long enough run a Map Reduce
job to count word occurences by each County, State and the entire US.

+ See `geotweet/mapreduce/wordcount/geo.py` for GeoWordCount map reduce job
+ See `bin/mapreduce_runner.sh` for an example of running local and EMR jobs
+ See `example_conf/mrjob.conf` for config required to run an EMR job


### Dependencies

+ python `requirements.txt` need to be installed


### Run Scripts as Daemon

If running on Ubuntu you can set the **environment variables** in
`example_conf/streamer.conf` and `example_conf/s3listener.conf`,
and copy those files to `/etc/init/`

To start them as a service run:
```
sudo service streamer start
sudo service s3listener start
```


### RETIRED: Load Geographic Data into MongoDB

#### Build VM with MongoDB using Virtualbox

Make sure you have the Ubuntu 14.04 (`ubuntu/trusty64`) vagrant box installed.

```bash
git clone https://github.com/meyersj/geotweet.git
cd geotweet
vagrant up
```

If everything worked, MongoDB should be accessible at
`mongodb://127.0.0.1:27017`.

```
vagrant ssh

# load mongo with geo data
cd /vagrant/bin
python loader.py osm /vagrant/data/states.txt   # load OSM POI nodes
python loader.py boundary                       # load State and County GeoJSONs
```

#### Load OSM POI Data in MongoDB

+ `java` and `osmosis` must be installed and on your path. [Osmosis Documentation](http://wiki.openstreetmap.org/wiki/Osmosis)
+ MongoDB needs to be installed
+ Environment variable `GEOTWEET_MONGODB_URI` must point to a live MongoDB instance

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

#### Load State and County Boundary Data in MongoDB

+ Environment variable `GEOTWEET_MONGODB_URI` must point to a live MongoDB instance

Load US states and counties boundary geometry as GeoJSON documents
into MongoDB.

**Run**: `python bin/loader.py boundary`
