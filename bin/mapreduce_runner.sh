#!/bin/bash

SCRIPTDIR=`dirname $(readlink -f $0)`
JOBDIR=`readlink -f ${SCRIPTDIR}/../geotweet/mapreduce`
DATADIR=`readlink -f ${SCRIPTDIR}/../geotweet/data/mapreduce`


# === MR Job Parameters ===

interpreter=../env/bin/python
script="${JOBDIR}/state_county_wordcount.py"

# ==========================


# Local Job
logfile="twitter-stream.log.2016-03-27_01-53"
src="${DATADIR}/${logfile}"
LOCAL_JOB_CMD="${interpreter} ${script} ${src}"


# EMR Job
now=`date +"%Y%m%d%H%M"`
src="s3://jeffrey.alan.meyers.geotweet-test/"
dst="--output-dir s3://jeffrey.alan.meyers.bucket/geotweet/output/geo-wordcount-${now}"
conf="--conf-path ~/scratch/mrjob.conf"
EMR_JOB_CMD="${interpreter} ${script} -r emr ${src} ${dst} --no-output"
EMR_JOB_CMD="${interpreter} ${script} -r emr ${conf} ${src} ${dst} --no-output"

# Run
#${LOCAL_JOB_CMD}
${EMR_JOB_CMD}
