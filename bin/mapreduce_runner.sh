#!/bin/bash

SCRIPTDIR=`dirname $(readlink -f $0)`
JOBDIR=`readlink -f ${SCRIPTDIR}/../geotweet/mapreduce/wordcount`
DATADIR=`readlink -f ${SCRIPTDIR}/../data/mapreduce`


# === MR Job Parameters ===

interpreter=python
script="${JOBDIR}/geo.py"

# ==========================


# Local Job
logfile="twitter-stream.log.2016-03-26_13-13"
src="${DATADIR}/${logfile}"
LOCAL_JOB_CMD="${interpreter} ${script} ${src}"

# EMR Job
src="s3://jeffrey.alan.meyers.geotweet/"
dst="s3://jeffrey.alan.meyers.geowordcount/geo-wordcount-output-all-2/"
EMR_JOB_CMD="${interpreter} ${script} ${src} -r emr --output-dir=${dst} --no-output"


# Run
${LOCAL_JOB_CMD}
#${EMR_JOB_CMD}
