#!/bin/bash

export GEOTWEET_LOG=/tmp/geotweet.log
export GEOTWEET_STREAM_DIR=/tmp/geotweet
export GEOTWEET_STREAM_LOG_INTERVAL=60   # minutes in each log file
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
