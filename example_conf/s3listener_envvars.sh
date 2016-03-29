#!/bin/bash

export GEOTWEET_LOG=/tmp/geotweet.log
export GEOTWEET_STREAM_DIR=/tmp/geotweet            # directory for log events

# get these from AWS
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="region"                  # example: "us-west-2"
export AWS_BUCKET="already.created.bucket.name"     # must already exist on S3
