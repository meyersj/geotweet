Geotweet
========

### License

MIT License. Copyright (c) 2016 Jeffrey Alan Meyers. See `LICENSE.md`


### About

This project contains python scripts to log tweets from the
[Twitter Streaming API](https://dev.twitter.com/streaming/reference/post/statuses/filter)
and load them into Amazon S3 Buckets.
The log files in S3 are then used as input for Elastic MapReduce jobs.

Also contains some scripts to extract POI nodes from OSM data and
load into MongoDB, as well as loading US states and routes GeoJSON into MongoDB.

### Dependencies

+ Python `requirements.txt` need to be installed with pip
+ To build a local vm, you need `virtualbox`/`vagrant` installed and the `ubuntu/trusty64` box

```
git clone https://github.com/meyersj/geotweet.git
cd geotweet
pip install -r requirements.txt   # it would be better to use a virtual environment
```

### Data Pipeline

#### 1. Extract Geographic Tweets **(Daemon)**

Python script running on a cheap VPS (DigitalOcean) will connect to the
*Twitter Streaming API* and filter for tweets inside Continental US.

For each tweet (if Lat-Lon coordinates are provided),
extract fields, marshal as JSON and append to a log file.
The log files are rotated every 60 minutes.

**Run**
```bash
cat example_conf/streamer_envvars.sh >> ~/.bashrc
vim ~/.bashrc                         # set all of the environment variables
source ~/.bashrc
python bin/streamer.py
```

**Run as Daemon using Upstart**
```bash
sudo cp example_conf/streamer.conf /etc/init/
sudo vim /etc/init/streamer.conf      # set all of the environment variables
sudo service streamer start
```

#### 2. Load Tweets into S3 **(Daemon)**

Another python script will be listening for the `streamer.py` log file rotations.
Each archived file will be uploaded into an Amazon S3 Bucket.

**Run**
```bash
cat example_conf/s3listener_envvars.sh >> ~/.bashrc
vim ~/.bashrc                         # set all of the environment variables
source ~/.bashrc
python bin/s3listener.py
```

**Run as Daemon using Upstart**
```bash
sudo cp example_conf/s3listener.conf /etc/init/
sudo vim /etc/init/s3listener.conf    # set all of the environment variables
sudo service s3listener start
```
**NOTE:** The `streaming.py` script must be raa at least once before `s3listener.py` script
to create the correct directory structure.

#### 3. Process with EMR **(Batch)**

After log files have been collected for long enough run a Map Reduce
job to count word occurences by each County, State and the entire US.

+ See `geotweet/mapreduce/wordcount/geo.py` for GeoWordCount map reduce job
+ See `bin/mapreduce_runner.sh` for an example of running local and EMR jobs
+ See `example_conf/mrjob.conf` for config required to run an EMR job

**Local**
```bash
cd geotweet/mapreduce/wordcount

# run geo wordcount job with sample data
python geo.py ../../../data/mapreduce/twitter-stream.log.2016-03-26_13-13
```

**EMR**
```bash
cp example_conf/mrjob.conf ~/.mrjob.conf
vim ~/.mrjob.conf       # set all of the config parameters, make sure all example paths are corrected
cd geotweet/mapreduce/wordcount
src=s3://some.s3.bucket/input                               # folder containing logs from `streamer.py`
dst=s3://some.s3.bucket/output/<new folder>                 # the new folder should not already exist
python geo.py $src -r emr --output-dir=$dst --no-output     # supress output to stdout (will go to s3)   
```

### Load Geographic Data into MongoDB

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

**Run**: `python bin/loader.py osm [/path/to/states.txt]`

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
