#!/bin/bash

SCRIPTDIR=`dirname $(readlink -f $0)`
DATADIR=`readlink -f ${SCRIPTDIR}/../data/mapreduce`


# === MR Job Parameters ===

interpreter=python
script="us-state-county-wordcount-v2.py"

# ==========================

logfile="twitter-stream.log.2016-03-26_13-13"

# Local Job
src="${DATADIR}/${logfile}"
LOCAL_JOB_CMD="${interpreter} ${script} ${src}"

# EMR Job
src="s3://jeffrey.alan.meyers.geotweet/"
dst="s3://jeffrey.alan.meyers.geowordcount/geo-wordcount-output-all/"
EMR_JOB_CMD="${interpreter} ${script} ${src} -r emr --output-dir=${dst} --no-output"


# Run
#${LOCAL_JOB_CMD}
${EMR_JOB_CMD}
